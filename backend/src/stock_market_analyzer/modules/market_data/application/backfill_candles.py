from __future__ import annotations

from dataclasses import dataclass

from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.candle_repository import CandleRepository
from stock_market_analyzer.modules.market_data.ports.market_data_provider import MarketDataProvider


@dataclass(frozen=True, slots=True)
class BackfillCandles:
    provider: MarketDataProvider
    repository: CandleRepository
    data_source: str

    def execute(
        self,
        *,
        instrument_id: str,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> int:
        candles = self.provider.get_candles(symbol, interval, period)
        return self.repository.upsert(
            instrument_id,
            interval,
            candles,
            data_source=self.data_source,
        )
