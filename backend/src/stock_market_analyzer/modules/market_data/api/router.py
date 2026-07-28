from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import AbstractContextManager, ExitStack
from datetime import UTC, datetime
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
from stock_market_analyzer.modules.market_data.application.stream_candles import StreamCandles
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataDependencyError,
    MarketDataProvider,
    SymbolNotSupportedError,
)
from stock_market_analyzer.shared.kernel.errors.api_error import ApiError

MarketDataProviderFactory = Callable[[], AbstractContextManager[MarketDataProvider]]


def create_market_data_router(
    *,
    provider_factory: MarketDataProviderFactory,
    data_source: str,
    stream_interval_seconds: float,
) -> APIRouter:
    if stream_interval_seconds < 0:
        raise ValueError("Market-data stream interval must not be negative.")

    router = APIRouter(prefix="/market-data", tags=["market-data"])

    @router.get(
        "/candles",
        operation_id="getMarketDataCandles",
        summary="Get historical candles",
        description="Return canonical UTC OHLCV candles for a supported symbol and timeframe.",
        response_model=CandleSeriesResponse,
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
        "/stream",
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
        provider_stack = ExitStack()
        try:
            provider = provider_stack.enter_context(provider_factory())
            updates = StreamCandles(provider).execute(symbol, interval)
        except (InvalidMarketDataRequest, SymbolNotSupportedError) as exc:
            provider_stack.close()
            _raise_api_error(exc)
        except MarketDataDependencyError as exc:
            provider_stack.close()
            _raise_api_error(exc)

        return StreamingResponse(
            _stream_events(
                updates=updates,
                provider_stack=provider_stack,
                symbol=symbol.strip().upper(),
                interval=interval,
                stream_interval_seconds=stream_interval_seconds,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return router


async def _stream_events(
    *,
    updates: Iterator[Candle],
    provider_stack: ExitStack,
    symbol: str,
    interval: Interval,
    stream_interval_seconds: float,
) -> AsyncIterator[str]:
    try:
        for sequence, candle in enumerate(updates, start=1):
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


def _raise_api_error(exc: Exception) -> Never:
    if isinstance(exc, MarketDataDependencyError):
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
