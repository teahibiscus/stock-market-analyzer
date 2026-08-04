from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval


@runtime_checkable
class CandleRepository(Protocol):
    def get_range(
        self,
        instrument_id: str,
        interval: Interval,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[Candle]:
        """Return canonical candles in ascending timestamp order."""
        ...

    def upsert(
        self,
        instrument_id: str,
        interval: Interval,
        candles: list[Candle],
        *,
        data_source: str,
        adjustment_version: int = 1,
    ) -> int:
        """Persist candles idempotently and return the number processed."""
        ...
