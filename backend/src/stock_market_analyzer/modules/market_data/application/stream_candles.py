from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from stock_market_analyzer.modules.market_data.application.get_candles import normalize_symbol
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataProvider,
)


@dataclass(frozen=True, slots=True)
class StreamCandles:
    provider: MarketDataProvider

    def execute(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        return self.provider.iter_updates(normalize_symbol(symbol), interval)
