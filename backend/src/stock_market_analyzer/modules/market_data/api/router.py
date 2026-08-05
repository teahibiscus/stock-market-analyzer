from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import AbstractContextManager, ExitStack
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Annotated, Never

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from stock_market_analyzer.modules.market_data.api.schemas import (
    CandleSeriesResponse,
    StreamCandleUpdate,
)
from stock_market_analyzer.modules.market_data.application.get_candles import (
    GetCandles,
    InvalidMarketDataRequest,
)
from stock_market_analyzer.modules.market_data.application.get_instrument_candles import (
    GetInstrumentCandles,
)
from stock_market_analyzer.modules.market_data.application.stream_candles import StreamCandles
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.candle_repository import CandleRepository
from stock_market_analyzer.modules.market_data.ports.instrument_resolver import (
    InstrumentNotFoundError,
    InstrumentResolver,
)
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataDependencyError,
    MarketDataPersistenceError,
    MarketDataProvider,
    SymbolNotSupportedError,
)
from stock_market_analyzer.shared.kernel.errors.api_error import ApiError

MarketDataProviderFactory = Callable[[], AbstractContextManager[MarketDataProvider]]
CandleRepositoryFactory = Callable[[], AbstractContextManager[CandleRepository]]
InstrumentResolverFactory = Callable[[], AbstractContextManager[InstrumentResolver]]


def create_market_data_router(
    *,
    provider_factory: MarketDataProviderFactory,
    data_source: str,
    stream_interval_seconds: float,
    repository_factory: CandleRepositoryFactory | None = None,
    instrument_resolver_factory: InstrumentResolverFactory | None = None,
    stream_max_seconds: float = 300.0,
    stream_max_connections: int = 20,
) -> APIRouter:
    if stream_interval_seconds < 0:
        raise ValueError("Market-data stream interval must not be negative.")

    if stream_max_seconds <= 0 or stream_max_connections < 1:
        raise ValueError("Market-data stream limits must be positive.")
    limiter = _ConnectionLimiter(stream_max_connections)
    router = APIRouter(tags=["market-data"])

    @router.get(
        "/market-data/candles",
        operation_id="getMarketDataCandles",
        summary="Get historical candles",
        description="Return canonical UTC OHLCV candles for a supported symbol and timeframe.",
        response_model=CandleSeriesResponse,
        deprecated=True,
        responses={
            422: {"description": "The symbol or timeframe is invalid or unsupported."},
            503: {"description": "Market data is temporarily unavailable."},
        },
    )
    def get_candles(
        symbol: Annotated[str, Query(max_length=20)],
        interval: Interval,
        period: Period,
    ) -> CandleSeriesResponse:
        try:
            with provider_factory() as provider:
                candles = GetCandles(provider).execute(symbol, interval, period)
        except (InvalidMarketDataRequest, SymbolNotSupportedError) as exc:
            _raise_api_error(exc)
        except MarketDataDependencyError as exc:
            _raise_api_error(exc)

        return CandleSeriesResponse.from_candles(
            symbol=symbol.strip().upper(),
            interval=interval,
            period=period,
            data_source=data_source,
            as_of=datetime.now(UTC),
            candles=candles,
        )

    @router.get(
        "/market-data/stream",
        operation_id="streamMarketDataCandles",
        summary="Stream candle updates",
        description="Stream canonical UTC OHLCV candle updates using Server-Sent Events.",
        response_class=StreamingResponse,
        responses={
            200: {
                "description": "Server-Sent Events containing candle updates.",
                "content": {"text/event-stream": {"schema": {"type": "string"}}},
            },
            422: {"description": "The symbol or interval is invalid or unsupported."},
            503: {"description": "Market data is temporarily unavailable."},
        },
    )
    def stream_candles(
        symbol: Annotated[str, Query(max_length=20)],
        interval: Interval,
    ) -> StreamingResponse:
        if not limiter.acquire():
            raise ApiError(
                code="DEPENDENCY_ERROR",
                message="Too many active market-data streams.",
                status_code=503,
                recoverable=True,
            )
        provider_stack = ExitStack()
        try:
            provider = provider_stack.enter_context(provider_factory())
            updates = StreamCandles(provider).execute(symbol, interval)
        except (InvalidMarketDataRequest, SymbolNotSupportedError) as exc:
            provider_stack.close()
            limiter.release()
            _raise_api_error(exc)
        except MarketDataDependencyError as exc:
            provider_stack.close()
            limiter.release()
            _raise_api_error(exc)

        return StreamingResponse(
            _stream_events(
                updates=updates,
                provider_stack=provider_stack,
                symbol=symbol.strip().upper(),
                interval=interval,
                stream_interval_seconds=stream_interval_seconds,
                stream_max_seconds=stream_max_seconds,
                release_connection=limiter.release,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @router.get(
        "/charts/{instrument_id}",
        operation_id="getInstrumentChart",
        summary="Get an instrument chart",
        response_model=CandleSeriesResponse,
        responses={
            422: {"description": "The instrument or timeframe is invalid."},
            503: {"description": "Canonical market data is temporarily unavailable."},
        },
    )
    def get_instrument_chart(
        instrument_id: str,
        interval: Interval,
        period: Period,
    ) -> CandleSeriesResponse:
        if repository_factory is None or instrument_resolver_factory is None:
            raise ApiError(
                code="DEPENDENCY_ERROR",
                message="Canonical market data is not configured.",
                status_code=503,
                recoverable=True,
            )
        try:
            with ExitStack() as stack:
                provider = stack.enter_context(provider_factory())
                repository = stack.enter_context(repository_factory())
                resolver = stack.enter_context(instrument_resolver_factory())
                series = GetInstrumentCandles(
                    provider=provider,
                    repository=repository,
                    resolver=resolver,
                    data_source=data_source,
                ).execute(instrument_id, interval, period)
        except (InstrumentNotFoundError, InvalidMarketDataRequest, SymbolNotSupportedError) as exc:
            _raise_api_error(exc)
        except (MarketDataDependencyError, MarketDataPersistenceError) as exc:
            _raise_api_error(exc)

        return CandleSeriesResponse.from_candles(
            instrument_id=series.instrument_id,
            symbol=series.symbol,
            interval=interval,
            period=period,
            data_source=data_source,
            as_of=datetime.now(UTC),
            candles=series.candles,
            read_through=series.read_through,
        )

    return router


async def _stream_events(
    *,
    updates: Iterator[Candle],
    provider_stack: ExitStack,
    symbol: str,
    interval: Interval,
    stream_interval_seconds: float,
    stream_max_seconds: float,
    release_connection: Callable[[], None],
) -> AsyncIterator[str]:
    started_at = monotonic()
    try:
        yield ": heartbeat\n\n"
        for sequence, candle in enumerate(updates, start=1):
            if monotonic() - started_at >= stream_max_seconds:
                break
            update = StreamCandleUpdate.from_candle(
                symbol=symbol,
                interval=interval,
                candle=candle,
                event_timestamp=datetime.now(UTC),
                sequence=sequence,
            )
            yield (
                f"event: candle\nid: {sequence}\ndata: {update.model_dump_json(by_alias=True)}\n\n"
            )
            if stream_interval_seconds:
                await asyncio.sleep(stream_interval_seconds)
    finally:
        provider_stack.close()
        release_connection()


def _raise_api_error(exc: Exception) -> Never:
    if isinstance(exc, (MarketDataDependencyError, MarketDataPersistenceError)):
        raise ApiError(
            code="DEPENDENCY_ERROR",
            message="Market data is temporarily unavailable.",
            status_code=503,
            recoverable=True,
        ) from exc
    if isinstance(exc, SymbolNotSupportedError):
        message = "Symbol is not supported for market data."
    else:
        message = str(exc)
    raise ApiError(
        code="VALIDATION_ERROR",
        message=message,
        status_code=422,
        recoverable=True,
    ) from exc


class _ConnectionLimiter:
    def __init__(self, maximum: int) -> None:
        self._maximum = maximum
        self._active = 0
        self._lock = Lock()

    def acquire(self) -> bool:
        with self._lock:
            if self._active >= self._maximum:
                return False
            self._active += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)
