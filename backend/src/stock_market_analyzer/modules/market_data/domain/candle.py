from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    @classmethod
    def create(
        cls,
        *,
        timestamp: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: int,
    ) -> Candle:
        if timestamp.utcoffset() != timedelta(0):
            raise ValueError("Candle timestamp must be timezone-aware UTC.")
        if high < low:
            raise ValueError("High price must be greater than or equal to low price.")
        if high < open or high < close:
            raise ValueError("High price must not be below open or close.")
        if low > open or low > close:
            raise ValueError("Low price must not be above open or close.")
        if volume < 0:
            raise ValueError("Volume must not be negative.")

        return cls(
            timestamp=timestamp.astimezone(UTC),
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
