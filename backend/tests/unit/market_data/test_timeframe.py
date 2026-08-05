from stock_market_analyzer.modules.market_data.domain.timeframe import (
    SUPPORTED_COMBINATIONS,
    Interval,
    Period,
    interval_seconds,
    is_supported,
)


def test_every_interval_has_an_explicit_duration() -> None:
    assert {interval: interval_seconds(interval) for interval in Interval} == {
        Interval.ONE_MINUTE: 60,
        Interval.TWO_MINUTES: 120,
        Interval.FIVE_MINUTES: 300,
        Interval.FIFTEEN_MINUTES: 900,
        Interval.THIRTY_MINUTES: 1_800,
        Interval.ONE_HOUR: 3_600,
        Interval.ONE_DAY: 86_400,
    }


def test_supported_combinations_are_explicit_for_every_interval() -> None:
    assert {
        Interval.ONE_MINUTE: frozenset({Period.ONE_DAY, Period.FIVE_DAYS}),
        Interval.TWO_MINUTES: frozenset({Period.ONE_DAY, Period.FIVE_DAYS}),
        Interval.FIVE_MINUTES: frozenset({Period.ONE_DAY, Period.FIVE_DAYS, Period.ONE_MONTH}),
        Interval.FIFTEEN_MINUTES: frozenset({Period.ONE_DAY, Period.FIVE_DAYS, Period.ONE_MONTH}),
        Interval.THIRTY_MINUTES: frozenset({Period.ONE_DAY, Period.FIVE_DAYS, Period.ONE_MONTH}),
        Interval.ONE_HOUR: frozenset(
            {
                Period.ONE_DAY,
                Period.FIVE_DAYS,
                Period.ONE_MONTH,
                Period.THREE_MONTHS,
                Period.SIX_MONTHS,
            }
        ),
        Interval.ONE_DAY: frozenset(
            {
                Period.ONE_MONTH,
                Period.THREE_MONTHS,
                Period.SIX_MONTHS,
                Period.ONE_YEAR,
            }
        ),
    } == SUPPORTED_COMBINATIONS


def test_supported_combination_lookup_handles_valid_and_invalid_pairs() -> None:
    assert is_supported(Interval.ONE_MINUTE, Period.ONE_DAY)
    assert not is_supported(Interval.ONE_MINUTE, Period.ONE_MONTH)
    assert not is_supported(Interval.ONE_DAY, Period.ONE_DAY)
    assert is_supported(Interval.ONE_DAY, Period.ONE_YEAR)
