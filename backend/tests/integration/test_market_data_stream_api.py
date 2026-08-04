from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from stock_market_analyzer.app.api.exception_handlers import (
    ExceptionHandler,
    api_error_exception_handler,
    validation_exception_handler,
)
from stock_market_analyzer.app.middleware.correlation_id import CorrelationIdMiddleware
from stock_market_analyzer.modules.market_data.api.router import create_market_data_router
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataDependencyError,
    MarketDataProviderError,
    SymbolNotSupportedError,
)
from stock_market_analyzer.shared.kernel.errors.api_error import ApiError


class ContextState:
    def __init__(self) -> None:
        self.entered = False
        self.open = False
        self.exited = False


class FiniteStreamProvider:
    def __init__(
        self,
        state: ContextState,
        *,
        updates: tuple[Candle, ...] = (),
        error: MarketDataProviderError | None = None,
    ) -> None:
        self.state = state
        self.updates = updates
        self.error = error

    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        return []

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        if self.error is not None:
            raise self.error

        def generate() -> Iterator[Candle]:
            for update in self.updates:
                assert self.state.open
                yield update

        return generate()


def _candle(minute: int, close: str) -> Candle:
    price = Decimal(close)
    return Candle.create(
        timestamp=datetime(2026, 7, 24, 15, minute, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=100 + minute,
    )


def _client(provider: FiniteStreamProvider, state: ContextState) -> TestClient:
    @contextmanager
    def provide() -> Iterator[FiniteStreamProvider]:
        state.entered = True
        state.open = True
        try:
            yield provider
        finally:
            state.open = False
            state.exited = True

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(
        create_market_data_router(
            provider_factory=provide,
            data_source="demo",
            stream_interval_seconds=0,
        ),
        prefix="/api/v1",
    )
    app.add_exception_handler(ApiError, cast(ExceptionHandler, api_error_exception_handler))
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_exception_handler),
    )
    return TestClient(app)


def _events(response_text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for block in response_text.strip().split("\n\n"):
        if block.startswith(":"):
            continue
        lines = block.splitlines()
        events.append(
            {
                "event": lines[0].removeprefix("event: "),
                "id": lines[1].removeprefix("id: "),
                "data": json.loads(lines[2].removeprefix("data: ")),
            }
        )
    return events


def test_stream_endpoint_emits_ordered_parseable_events_and_closes_context() -> None:
    state = ContextState()
    provider = FiniteStreamProvider(
        state,
        updates=(_candle(30, "210.00"), _candle(31, "210.25")),
    )

    response = _client(provider, state).get(
        "/api/v1/market-data/stream",
        params={"symbol": "AAPL", "interval": "1m"},
    )
    events = _events(response.text)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert response.text.startswith(": heartbeat\n\n")
    assert [event["event"] for event in events] == ["candle", "candle"]
    assert [event["id"] for event in events] == ["1", "2"]
    assert [event["data"]["sequence"] for event in events] == [1, 2]  # type: ignore[index]
    assert [event["data"]["close"] for event in events] == ["210.00", "210.25"]  # type: ignore[index]
    assert str(events[0]["data"]["timestamp"]).endswith("Z")  # type: ignore[index]
    assert str(events[0]["data"]["eventTimestamp"]).endswith("Z")  # type: ignore[index]
    assert state.entered is True
    assert state.exited is True
    assert state.open is False


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (SymbolNotSupportedError("private symbol detail"), 422, "VALIDATION_ERROR"),
        (MarketDataDependencyError("private dependency detail"), 503, "DEPENDENCY_ERROR"),
    ],
)
def test_stream_endpoint_maps_errors_before_streaming(
    error: MarketDataProviderError,
    status_code: int,
    code: str,
) -> None:
    state = ContextState()
    response = _client(FiniteStreamProvider(state, error=error), state).get(
        "/api/v1/market-data/stream",
        params={"symbol": "MSFT", "interval": "1m"},
    )

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == code
    assert "private" not in response.json()["detail"]
    assert state.exited is True
