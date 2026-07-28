from __future__ import annotations

from dataclasses import dataclass

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import (
    Interval,
    Period,
    is_supported,
)
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataProvider,
)


class InvalidMarketDataRequest(ValueError):
    """The requested market-data operation is invalid."""


class InvalidMarketDataSymbol(InvalidMarketDataRequest):
    """The request does not contain a usable symbol."""


class UnsupportedCandleCombination(InvalidMarketDataRequest):
    """The requested candle interval and period cannot be combined."""


@dataclass(frozen=True, slots=True)
class GetCandles:
    provider: MarketDataProvider

    def execute(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        normalized_symbol = normalize_symbol(symbol)
        if not is_supported(interval, period):
            raise UnsupportedCandleCombination(
                f"Interval {interval.value} is not supported for period {period.value}."
            )
        return self.provider.get_candles(normalized_symbol, interval, period)


def normalize_symbol(symbol: str) -> str:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise InvalidMarketDataSymbol("Symbol must not be empty.")
    return normalized_symbol
