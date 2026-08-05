from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient

from stock_market_analyzer.modules.market_data.api.router import create_market_data_router
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.ports.instrument_resolver import ResolvedInstrument

INSTRUMENT_ID = "00000000-0000-4000-8000-000000000002"


class FakeProvider:
    def get_candles(self, symbol: str, interval: object, period: object) -> list[Candle]:
        return [_candle()]

    def iter_updates(self, symbol: str, interval: object):  # type: ignore[no-untyped-def]
        return iter([_candle()])


class FakeRepository:
    def __init__(self) -> None:
        self.saved = False

    def get_range(self, *args: object, **kwargs: object) -> list[Candle]:
        return []

    def upsert(self, *args: object, **kwargs: object) -> int:
        self.saved = True
        return 1


class FakeResolver:
    def resolve(self, instrument_id: str) -> ResolvedInstrument:
        return ResolvedInstrument(instrument_id=instrument_id, symbol="MSFT")


def test_chart_endpoint_resolves_instrument_and_persists_read_through() -> None:
    repository = FakeRepository()
    app = FastAPI()
    app.include_router(
        create_market_data_router(
            provider_factory=lambda: nullcontext(FakeProvider()),
            repository_factory=lambda: nullcontext(repository),
            instrument_resolver_factory=lambda: nullcontext(FakeResolver()),
            data_source="demo",
            stream_interval_seconds=0,
        ),
        prefix="/api/v1",
    )

    response = TestClient(app).get(
        f"/api/v1/charts/{INSTRUMENT_ID}",
        params={"interval": "1d", "period": "1y"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["instrumentId"] == INSTRUMENT_ID
    assert payload["symbol"] == "MSFT"
    assert payload["metadata"]["freshness"]["state"] == "STALE"
    assert payload["metadata"]["warnings"] == [
        "SYNTHETIC_MARKET_DATA",
        "MARKET_DATA_READ_THROUGH",
    ]
    assert repository.saved is True


def _candle() -> Candle:
    return Candle.create(
        timestamp=datetime(2026, 7, 28, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=1_000,
    )
