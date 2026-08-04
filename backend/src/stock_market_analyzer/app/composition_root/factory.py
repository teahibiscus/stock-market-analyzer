from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from functools import partial
from typing import cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from stock_market_analyzer.app.api.exception_handlers import (
    ExceptionHandler,
    api_error_exception_handler,
    validation_exception_handler,
)
from stock_market_analyzer.app.api.router import api_v1_router
from stock_market_analyzer.app.api.routes.health import create_health_router
from stock_market_analyzer.app.composition_root.instrument_resolver import (
    SqlAlchemyInstrumentResolver,
)
from stock_market_analyzer.app.middleware.correlation_id import CorrelationIdMiddleware
from stock_market_analyzer.config.settings import Settings, get_settings
from stock_market_analyzer.modules.instruments.api.router import (
    InstrumentProviderFactory,
    create_instrument_router,
)
from stock_market_analyzer.modules.instruments.infrastructure.persistence.repository import (
    SqlAlchemyInstrumentRepository,
)
from stock_market_analyzer.modules.instruments.ports.instrument_reference_provider import (
    InstrumentReferenceProvider,
)
from stock_market_analyzer.modules.market_data.api.router import (
    CandleRepositoryFactory,
    InstrumentResolverFactory,
    MarketDataProviderFactory,
    create_market_data_router,
)
from stock_market_analyzer.modules.market_data.infrastructure.persistence.repository import (
    SqlAlchemyCandleRepository,
)
from stock_market_analyzer.modules.market_data.infrastructure.provider.demo_provider import (
    DemoMarketDataProvider,
)
from stock_market_analyzer.modules.market_data.ports.candle_repository import CandleRepository
from stock_market_analyzer.modules.market_data.ports.instrument_resolver import InstrumentResolver
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataProvider,
)
from stock_market_analyzer.shared.infrastructure.cache.health import (
    check_cache_health,
    create_redis_client,
)
from stock_market_analyzer.shared.infrastructure.database.health import (
    check_database_health,
    create_database_engine,
)
from stock_market_analyzer.shared.infrastructure.telemetry.logging import configure_logging
from stock_market_analyzer.shared.kernel.errors.api_error import ApiError


def create_app(
    *,
    settings: Settings | None = None,
    database_health_checker: Callable[[], bool] | None = None,
    cache_health_checker: Callable[[], bool] | None = None,
    instrument_reference_provider: InstrumentReferenceProvider | None = None,
    market_data_provider: MarketDataProvider | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)

    database_engine = create_database_engine(resolved_settings)
    if database_health_checker is None:
        database_health_checker = partial(check_database_health, database_engine)

    if cache_health_checker is None:
        redis_client = create_redis_client(resolved_settings)
        cache_health_checker = partial(check_cache_health, redis_client)

    if instrument_reference_provider is not None:
        provider_factory = _constant_provider_factory(instrument_reference_provider)
    else:
        provider_factory = _repository_provider_factory(database_engine)

    market_data_provider_factory = _constant_market_data_provider_factory(
        market_data_provider or DemoMarketDataProvider()
    )
    frontend_origins = list(
        dict.fromkeys(
            origin
            for origin in (
                resolved_settings.frontend_origin,
                resolved_settings.frontend_additional_origin,
            )
            if origin is not None
        )
    )

    app = FastAPI(title=resolved_settings.app_name)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=frontend_origins,
        allow_methods=["GET"],
        allow_headers=["Content-Type", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
    )
    app.include_router(
        create_health_router(
            database_health_checker=database_health_checker,
            cache_health_checker=cache_health_checker,
        )
    )
    app.include_router(api_v1_router)
    app.include_router(
        create_instrument_router(
            provider_factory=provider_factory,
            result_limit=resolved_settings.instrument_search_limit,
        ),
        prefix="/api/v1",
    )
    app.include_router(
        create_market_data_router(
            provider_factory=market_data_provider_factory,
            data_source=resolved_settings.market_data_source,
            stream_interval_seconds=resolved_settings.market_data_stream_interval_seconds,
            repository_factory=_candle_repository_factory(database_engine),
            instrument_resolver_factory=_instrument_resolver_factory(database_engine),
            stream_max_seconds=resolved_settings.market_data_stream_max_seconds,
            stream_max_connections=resolved_settings.market_data_stream_max_connections,
        ),
        prefix="/api/v1",
    )

    app.add_exception_handler(ApiError, cast(ExceptionHandler, api_error_exception_handler))
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_exception_handler),
    )

    return app


def _constant_provider_factory(
    provider: InstrumentReferenceProvider,
) -> InstrumentProviderFactory:
    def provide() -> nullcontext[InstrumentReferenceProvider]:
        return nullcontext(provider)

    return provide


def _constant_market_data_provider_factory(
    provider: MarketDataProvider,
) -> MarketDataProviderFactory:
    def provide() -> nullcontext[MarketDataProvider]:
        return nullcontext(provider)

    return provide


def _repository_provider_factory(engine: Engine) -> InstrumentProviderFactory:
    database_session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def provide() -> Iterator[InstrumentReferenceProvider]:
        with database_session_factory() as session:
            yield SqlAlchemyInstrumentRepository(session)

    return provide


def _candle_repository_factory(engine: Engine) -> CandleRepositoryFactory:
    database_session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def provide() -> Iterator[CandleRepository]:
        with database_session_factory() as session:
            yield SqlAlchemyCandleRepository(session)

    return provide


def _instrument_resolver_factory(engine: Engine) -> InstrumentResolverFactory:
    database_session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def provide() -> Iterator[InstrumentResolver]:
        with database_session_factory() as session:
            yield SqlAlchemyInstrumentResolver(session)

    return provide
