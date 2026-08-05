from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.candle_repository import CandleRepository
from stock_market_analyzer.modules.market_data.ports.instrument_resolver import InstrumentResolver
from stock_market_analyzer.modules.market_data.ports.market_data_provider import MarketDataProvider

_PERIOD_DAYS: dict[Period, int] = {
    Period.ONE_DAY: 1,
    Period.FIVE_DAYS: 5,
    Period.ONE_MONTH: 30,
    Period.THREE_MONTHS: 90,
    Period.SIX_MONTHS: 180,
    Period.ONE_YEAR: 365,
}


@dataclass(frozen=True, slots=True)
class InstrumentCandleSeries:
    instrument_id: str
    symbol: str
    candles: list[Candle]
    read_through: bool


@dataclass(frozen=True, slots=True)
class GetInstrumentCandles:
    provider: MarketDataProvider
    repository: CandleRepository
    resolver: InstrumentResolver
    data_source: str
    result_limit: int = 500

    def execute(
        self,
        instrument_id: str,
        interval: Interval,
        period: Period,
        *,
        now: datetime | None = None,
    ) -> InstrumentCandleSeries:
        resolved = self.resolver.resolve(instrument_id)
        end = now or datetime.now(UTC)
        start = end - timedelta(days=_PERIOD_DAYS[period])
        candles = self.repository.get_range(
            instrument_id,
            interval,
            start=start,
            end=end,
            limit=self.result_limit,
        )
        read_through = not candles
        if read_through:
            candles = self.provider.get_candles(resolved.symbol, interval, period)
            self.repository.upsert(
                instrument_id,
                interval,
                candles,
                data_source=self.data_source,
            )
        return InstrumentCandleSeries(
            instrument_id=resolved.instrument_id,
            symbol=resolved.symbol,
            candles=candles,
            read_through=read_through,
        )
