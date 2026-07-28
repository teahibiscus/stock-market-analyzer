from datetime import UTC, datetime
from decimal import Decimal

from stock_market_analyzer.modules.market_data.domain.aggregation import bucket_start, merge_tick
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval


def test_bucket_start_floors_to_each_interval_in_utc() -> None:
    timestamp = datetime(2026, 7, 24, 12, 37, 42, 123456, tzinfo=UTC)

    assert bucket_start(timestamp, Interval.ONE_MINUTE) == datetime(2026, 7, 24, 12, 37, tzinfo=UTC)
    assert bucket_start(timestamp, Interval.TWO_MINUTES) == datetime(
        2026, 7, 24, 12, 36, tzinfo=UTC
    )
    assert bucket_start(timestamp, Interval.FIVE_MINUTES) == datetime(
        2026, 7, 24, 12, 35, tzinfo=UTC
    )
    assert bucket_start(timestamp, Interval.FIFTEEN_MINUTES) == datetime(
        2026, 7, 24, 12, 30, tzinfo=UTC
    )
    assert bucket_start(timestamp, Interval.THIRTY_MINUTES) == datetime(
        2026, 7, 24, 12, 30, tzinfo=UTC
    )
    assert bucket_start(timestamp, Interval.ONE_HOUR) == datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
    assert bucket_start(timestamp, Interval.ONE_DAY) == datetime(2026, 7, 24, tzinfo=UTC)


def test_merge_tick_updates_ohlcv_inside_the_active_bucket() -> None:
    first = merge_tick(
        None,
        timestamp=datetime(2026, 7, 24, 12, 37, 5, tzinfo=UTC),
        price=Decimal("213.10"),
        volume=100,
        interval=Interval.ONE_MINUTE,
    )

    second = merge_tick(
        first,
        timestamp=datetime(2026, 7, 24, 12, 37, 40, tzinfo=UTC),
        price=Decimal("213.35"),
        volume=25,
        interval=Interval.ONE_MINUTE,
    )
    updated = merge_tick(
        second,
        timestamp=datetime(2026, 7, 24, 12, 37, 55, tzinfo=UTC),
        price=Decimal("212.95"),
        volume=10,
        interval=Interval.ONE_MINUTE,
    )

    assert updated.timestamp == datetime(2026, 7, 24, 12, 37, tzinfo=UTC)
    assert updated.open == Decimal("213.10")
    assert updated.high == Decimal("213.35")
    assert updated.low == Decimal("212.95")
    assert updated.close == Decimal("212.95")
    assert updated.volume == 135


def test_merge_tick_starts_a_new_candle_across_a_bucket_boundary() -> None:
    active = merge_tick(
        None,
        timestamp=datetime(2026, 7, 24, 12, 37, 40, tzinfo=UTC),
        price=Decimal("213.10"),
        volume=100,
        interval=Interval.ONE_MINUTE,
    )

    next_candle = merge_tick(
        active,
        timestamp=datetime(2026, 7, 24, 12, 38, 1, tzinfo=UTC),
        price=Decimal("213.25"),
        volume=20,
        interval=Interval.ONE_MINUTE,
    )

    assert next_candle.timestamp == datetime(2026, 7, 24, 12, 38, tzinfo=UTC)
    assert next_candle.open == Decimal("213.25")
    assert next_candle.high == Decimal("213.25")
    assert next_candle.low == Decimal("213.25")
    assert next_candle.close == Decimal("213.25")
    assert next_candle.volume == 20
