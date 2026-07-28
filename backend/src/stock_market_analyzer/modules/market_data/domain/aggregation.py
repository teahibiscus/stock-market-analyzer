from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import (
    Interval,
    interval_seconds,
)


def bucket_start(timestamp: datetime, interval: Interval) -> datetime:
    utc_timestamp = _as_utc(timestamp)
    midnight = utc_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = int((utc_timestamp - midnight).total_seconds())
    bucket_offset = (seconds_since_midnight // interval_seconds(interval)) * interval_seconds(
        interval
    )
    return midnight + timedelta(seconds=bucket_offset)


def merge_tick(
    candle: Candle | None,
    *,
    timestamp: datetime,
    price: Decimal,
    volume: int,
    interval: Interval,
) -> Candle:
    timestamp_bucket = bucket_start(timestamp, interval)
    if candle is None or candle.timestamp != timestamp_bucket:
        return Candle.create(
            timestamp=timestamp_bucket,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=volume,
        )

    return Candle.create(
        timestamp=candle.timestamp,
        open=candle.open,
        high=max(candle.high, price),
        low=min(candle.low, price),
        close=price,
        volume=candle.volume + volume,
    )


def _as_utc(timestamp: datetime) -> datetime:
    if timestamp.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware.")
    return timestamp.astimezone(UTC)
