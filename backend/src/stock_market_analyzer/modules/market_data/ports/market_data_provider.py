from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period


class MarketDataProviderError(Exception):
    """Base failure exposed by market-data provider adapters."""


class SymbolNotSupportedError(MarketDataProviderError):
    """The provider does not supply data for the requested symbol."""


class MarketDataDependencyError(MarketDataProviderError):
    """An external market-data dependency is unavailable."""


class MarketDataPersistenceError(MarketDataProviderError):
    """Canonical market-data persistence could not complete an operation."""


@runtime_checkable
class MarketDataProvider(Protocol):
    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        """Return canonical historical candles in ascending timestamp order."""
        ...

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        """Yield canonical updates for the active and future candle buckets."""
        ...
