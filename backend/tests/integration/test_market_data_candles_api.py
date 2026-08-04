from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from stock_market_analyzer.app.composition_root.factory import create_app
from stock_market_analyzer.config.settings import Settings
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_provider import (
    SeedInstrumentReferenceProvider,
)
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataDependencyError,
    MarketDataProviderError,
    SymbolNotSupportedError,
)


class FakeMarketDataProvider:
    def __init__(
        self,
        *,
        candles: list[Candle] | None = None,
        error: MarketDataProviderError | None = None,
    ) -> None:
        self.candles = candles or []
        self.error = error

    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        if self.error is not None:
            raise self.error
        return self.candles

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        return iter(())


def _candle(minute: int, close: str) -> Candle:
    price = Decimal(close)
    return Candle.create(
        timestamp=datetime(2026, 7, 24, 15, minute, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=100,
    )


def _client(provider: FakeMarketDataProvider) -> TestClient:
    app = create_app(
        settings=Settings(
            market_data_source="demo",
            market_data_stream_interval_seconds=1,
        ),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
        market_data_provider=provider,
    )
    return TestClient(app)


def test_history_endpoint_returns_ordered_canonical_demo_response() -> None:
    client = _client(FakeMarketDataProvider(candles=[_candle(30, "210.00"), _candle(31, "210.25")]))

    response = client.get(
        "/api/v1/market-data/candles",
        params={"symbol": "AAPL", "interval": "1m", "period": "1d"},
        headers={"X-Correlation-ID": "candles-success"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "candles-success"
    assert payload["symbol"] == "AAPL"
    assert payload["interval"] == "1m"
    assert payload["period"] == "1d"
    assert payload["timezone"] == "UTC"
    assert payload["dataSource"] == "demo"
    assert [candle["timestamp"] for candle in payload["candles"]] == sorted(
        candle["timestamp"] for candle in payload["candles"]
    )
    assert payload["candles"][1]["close"] == "210.25"
    assert payload["metadata"]["state"] == "SUCCESS"
    assert payload["metadata"]["freshness"]["state"] == "STALE"


def test_history_endpoint_returns_empty_application_state() -> None:
    response = _client(FakeMarketDataProvider()).get(
        "/api/v1/market-data/candles",
        params={"symbol": "AAPL", "interval": "1d", "period": "1mo"},
    )

    assert response.status_code == 200
    assert response.json()["candles"] == []
    assert response.json()["metadata"]["state"] == "EMPTY"


@pytest.mark.parametrize(
    "params",
    [
        {"symbol": "   ", "interval": "1m", "period": "1d"},
        {"symbol": "AAPL", "interval": "3m", "period": "1d"},
        {"symbol": "AAPL", "interval": "1m", "period": "1mo"},
    ],
)
def test_history_endpoint_returns_problem_details_for_invalid_requests(
    params: dict[str, str],
) -> None:
    response = _client(FakeMarketDataProvider()).get(
        "/api/v1/market-data/candles",
        params=params,
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["recoverable"] is True


def test_history_endpoint_maps_unsupported_symbol_to_controlled_validation_error() -> None:
    response = _client(
        FakeMarketDataProvider(error=SymbolNotSupportedError("private provider detail"))
    ).get(
        "/api/v1/market-data/candles",
        params={"symbol": "MSFT", "interval": "1d", "period": "1mo"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "private provider detail" not in response.json()["detail"]


def test_history_endpoint_sanitizes_dependency_failures() -> None:
    response = _client(
        FakeMarketDataProvider(error=MarketDataDependencyError("secret upstream detail"))
    ).get(
        "/api/v1/market-data/candles",
        params={"symbol": "AAPL", "interval": "1d", "period": "1mo"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_ERROR"
    assert response.json()["recoverable"] is True
    assert "secret upstream detail" not in response.json()["detail"]


def test_existing_instrument_search_remains_operational() -> None:
    response = _client(FakeMarketDataProvider()).get(
        "/api/v1/instruments/search",
        params={"q": "Apple"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["symbol"] == "AAPL"
