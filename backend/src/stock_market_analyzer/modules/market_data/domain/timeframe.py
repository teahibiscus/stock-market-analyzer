from __future__ import annotations

from enum import StrEnum


class Interval(StrEnum):
    ONE_MINUTE = "1m"
    TWO_MINUTES = "2m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"


class Period(StrEnum):
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"


_INTERVAL_SECONDS: dict[Interval, int] = {
    Interval.ONE_MINUTE: 60,
    Interval.TWO_MINUTES: 120,
    Interval.FIVE_MINUTES: 300,
    Interval.FIFTEEN_MINUTES: 900,
    Interval.THIRTY_MINUTES: 1_800,
    Interval.ONE_HOUR: 3_600,
    Interval.ONE_DAY: 86_400,
}

SUPPORTED_COMBINATIONS: dict[Interval, frozenset[Period]] = {
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
}


def interval_seconds(interval: Interval) -> int:
    return _INTERVAL_SECONDS[interval]


def is_supported(interval: Interval, period: Period) -> bool:
    return period in SUPPORTED_COMBINATIONS[interval]
