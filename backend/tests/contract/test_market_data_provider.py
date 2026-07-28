from collections.abc import Iterator
from datetime import UTC, datetime

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.infrastructure.provider.demo_provider import (
    DemoMarketDataProvider,
)
from stock_market_analyzer.modules.market_data.ports.market_data_provider import MarketDataProvider


class FakeMarketDataProvider:
    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        return []

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        return iter(())


def test_market_data_provider_is_runtime_checkable() -> None:
    assert isinstance(FakeMarketDataProvider(), MarketDataProvider)
    assert isinstance(DemoMarketDataProvider(), MarketDataProvider)


def test_demo_provider_returns_canonical_candles() -> None:
    provider = DemoMarketDataProvider(clock=lambda: datetime(2026, 7, 24, 15, 30, tzinfo=UTC))

    candles = provider.get_candles("AAPL", Interval.ONE_DAY, Period.ONE_MONTH)

    assert candles
    assert all(isinstance(candle, Candle) for candle in candles)
