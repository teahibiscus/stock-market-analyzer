from collections.abc import Iterator

from stock_market_analyzer.app.composition_root.factory import create_app
from stock_market_analyzer.config.settings import Settings
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_provider import (
    SeedInstrumentReferenceProvider,
)
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period


class EmptyMarketDataProvider:
    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        return []

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        return iter(())


def test_market_data_openapi_contract_is_stable() -> None:
    app = create_app(
        settings=Settings(),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
        market_data_provider=EmptyMarketDataProvider(),
    )

    schema = app.openapi()
    paths = schema["paths"]
    history = paths["/api/v1/market-data/candles"]["get"]
    stream = paths["/api/v1/market-data/stream"]["get"]

    assert history["operationId"] == "getMarketDataCandles"
    assert stream["operationId"] == "streamMarketDataCandles"
    assert (
        history["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/CandleSeriesResponse"
    )
    assert "text/event-stream" in stream["responses"]["200"]["content"]
    candle_schema = schema["components"]["schemas"]["CandleSchema"]
    assert "volume" in candle_schema["required"]
    assert candle_schema["properties"]["volume"]["type"] == "integer"
    assert schema["components"]["schemas"]["Interval"]["enum"] == [
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "1h",
        "1d",
    ]
    assert schema["components"]["schemas"]["Period"]["enum"] == [
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
    ]
