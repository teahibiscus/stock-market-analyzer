from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from stock_market_analyzer.modules.market_data.domain.aggregation import bucket_start, merge_tick
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import (
    Interval,
    Period,
    interval_seconds,
    is_supported,
)
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    SymbolNotSupportedError,
)

HISTORY_CANDLE_LIMIT = 500
_SUPPORTED_SYMBOL = "AAPL"
_CENT = Decimal("0.01")
_MINIMUM_PRICE = Decimal("0.01")
_BASE_PRICE = Decimal("210.00")
_PERIOD_SECONDS: dict[Period, int] = {
    Period.ONE_DAY: 86_400,
    Period.FIVE_DAYS: 5 * 86_400,
    Period.ONE_MONTH: 30 * 86_400,
    Period.THREE_MONTHS: 90 * 86_400,
    Period.SIX_MONTHS: 180 * 86_400,
    Period.ONE_YEAR: 365 * 86_400,
}


class DemoMarketDataProvider:
    """Generate simulated development data; this is not live exchange market data."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or _utc_now

    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        normalized_symbol = _normalize_symbol(symbol)
        if not is_supported(interval, period):
            raise ValueError(
                f"Interval {interval.value} is not supported for period {period.value}."
            )

        candle_count = min(
            HISTORY_CANDLE_LIMIT,
            max(1, _PERIOD_SECONDS[period] // interval_seconds(interval)),
        )
        interval_delta = timedelta(seconds=interval_seconds(interval))
        final_timestamp = bucket_start(self._clock(), interval)
        first_timestamp = final_timestamp - interval_delta * (candle_count - 1)
        previous_close = _starting_price(normalized_symbol, interval, period, final_timestamp)
        candles: list[Candle] = []

        for index in range(candle_count):
            timestamp = first_timestamp + interval_delta * index
            key = (
                f"history|{normalized_symbol}|{interval.value}|{period.value}|"
                f"{timestamp.isoformat()}"
            )
            open_price = previous_close
            close_price = max(
                _MINIMUM_PRICE,
                open_price + _cents(_stable_int(f"{key}|move", -75, 75)),
            )
            high_price = max(open_price, close_price) + _cents(_stable_int(f"{key}|high", 0, 40))
            low_price = max(
                _MINIMUM_PRICE,
                min(open_price, close_price) - _cents(_stable_int(f"{key}|low", 0, 40)),
            )
            candles.append(
                Candle.create(
                    timestamp=timestamp,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=_stable_int(f"{key}|volume", 1_000, 100_000),
                )
            )
            previous_close = close_price

        return candles

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        normalized_symbol = _normalize_symbol(symbol)
        return self._generate_updates(normalized_symbol, interval)

    def _generate_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        active_candle: Candle | None = None
        sequence = 0

        while True:
            timestamp = self._clock()
            timestamp_bucket = bucket_start(timestamp, interval)
            key = f"update|{symbol}|{interval.value}|{timestamp_bucket.isoformat()}|{sequence}"
            if active_candle is None:
                price = _BASE_PRICE + _cents(_stable_int(f"{key}|start", -500, 500))
            else:
                price = max(
                    _MINIMUM_PRICE,
                    active_candle.close + _cents(_stable_int(f"{key}|move", -25, 25)),
                )

            active_candle = merge_tick(
                active_candle,
                timestamp=timestamp,
                price=price,
                volume=_stable_int(f"{key}|volume", 10, 100),
                interval=interval,
            )
            sequence += 1
            yield active_candle


def _normalize_symbol(symbol: str) -> str:
    normalized_symbol = symbol.strip().upper()
    if normalized_symbol != _SUPPORTED_SYMBOL:
        raise SymbolNotSupportedError(f"Symbol {normalized_symbol or symbol!r} is not supported.")
    return normalized_symbol


def _starting_price(
    symbol: str,
    interval: Interval,
    period: Period,
    final_timestamp: datetime,
) -> Decimal:
    key = f"start|{symbol}|{interval.value}|{period.value}|{final_timestamp.isoformat()}"
    return _BASE_PRICE + _cents(_stable_int(key, -500, 500))


def _cents(value: int) -> Decimal:
    return Decimal(value) * _CENT


def _stable_int(key: str, minimum: int, maximum: int) -> int:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return minimum + int.from_bytes(digest[:8], "big") % (maximum - minimum + 1)


def _utc_now() -> datetime:
    return datetime.now(UTC)
