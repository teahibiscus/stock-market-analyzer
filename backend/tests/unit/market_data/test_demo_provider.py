from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from stock_market_analyzer.modules.market_data.domain.aggregation import bucket_start
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.infrastructure.provider.demo_provider import (
    HISTORY_CANDLE_LIMIT,
    DemoMarketDataProvider,
)
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    SymbolNotSupportedError,
)

FIXED_NOW = datetime(2026, 7, 24, 15, 37, 42, tzinfo=UTC)


class SequenceClock:
    def __init__(self, timestamps: Iterable[datetime]) -> None:
        self._timestamps = iter(timestamps)

    def __call__(self) -> datetime:
        return next(self._timestamps)


def test_history_is_deterministic_for_the_same_request_and_clock() -> None:
    first = DemoMarketDataProvider(clock=lambda: FIXED_NOW).get_candles(
        "AAPL", Interval.ONE_MINUTE, Period.ONE_DAY
    )
    second = DemoMarketDataProvider(clock=lambda: FIXED_NOW).get_candles(
        "AAPL", Interval.ONE_MINUTE, Period.ONE_DAY
    )

    assert first == second


def test_history_is_bounded_ascending_unique_and_valid() -> None:
    candles = DemoMarketDataProvider(clock=lambda: FIXED_NOW).get_candles(
        "AAPL", Interval.ONE_MINUTE, Period.ONE_DAY
    )

    timestamps = [candle.timestamp for candle in candles]
    assert 0 < len(candles) <= HISTORY_CANDLE_LIMIT
    assert timestamps == sorted(timestamps)
    assert len(timestamps) == len(set(timestamps))
    assert all(timestamp.utcoffset() == timedelta(0) for timestamp in timestamps)
    assert all(
        candle.low <= candle.open <= candle.high
        and candle.low <= candle.close <= candle.high
        and candle.volume >= 0
        for candle in candles
    )
    assert all(
        isinstance(price, Decimal)
        for candle in candles
        for price in (candle.open, candle.high, candle.low, candle.close)
    )


@pytest.mark.parametrize(
    ("interval", "period"),
    [
        (Interval.FIVE_MINUTES, Period.ONE_DAY),
        (Interval.ONE_HOUR, Period.FIVE_DAYS),
        (Interval.ONE_DAY, Period.ONE_MONTH),
    ],
)
def test_history_timestamps_are_aligned_to_the_requested_interval(
    interval: Interval,
    period: Period,
) -> None:
    candles = DemoMarketDataProvider(clock=lambda: FIXED_NOW).get_candles("AAPL", interval, period)

    assert all(candle.timestamp == bucket_start(candle.timestamp, interval) for candle in candles)


def test_provider_accepts_lowercase_aapl() -> None:
    candles = DemoMarketDataProvider(clock=lambda: FIXED_NOW).get_candles(
        "aapl", Interval.ONE_DAY, Period.ONE_MONTH
    )

    assert candles


def test_provider_rejects_unsupported_symbols() -> None:
    provider = DemoMarketDataProvider(clock=lambda: FIXED_NOW)

    with pytest.raises(SymbolNotSupportedError, match="TSLA"):
        provider.get_candles("TSLA", Interval.ONE_DAY, Period.ONE_MONTH)
    with pytest.raises(SymbolNotSupportedError, match="TSLA"):
        provider.iter_updates("TSLA", Interval.ONE_MINUTE)


def test_provider_rejects_unsupported_interval_period_combination() -> None:
    provider = DemoMarketDataProvider(clock=lambda: FIXED_NOW)

    with pytest.raises(ValueError, match="not supported"):
        provider.get_candles("AAPL", Interval.ONE_MINUTE, Period.ONE_MONTH)


def test_updates_merge_inside_a_bucket_and_roll_at_the_boundary() -> None:
    provider = DemoMarketDataProvider(
        clock=SequenceClock(
            [
                datetime(2026, 7, 24, 12, 0, 5, tzinfo=UTC),
                datetime(2026, 7, 24, 12, 0, 40, tzinfo=UTC),
                datetime(2026, 7, 24, 12, 1, 1, tzinfo=UTC),
            ]
        )
    )
    updates = provider.iter_updates("AAPL", Interval.ONE_MINUTE)

    first = next(updates)
    second = next(updates)
    third = next(updates)

    assert second.timestamp == first.timestamp
    assert second.open == first.open
    assert second.volume > first.volume
    assert second.low <= second.close <= second.high

    assert third.timestamp > second.timestamp
    assert third.open == third.high == third.low == third.close
    assert third.volume > 0
