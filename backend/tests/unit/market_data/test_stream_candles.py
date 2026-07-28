from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from itertools import islice
from typing import cast

import pytest

from stock_market_analyzer.modules.market_data.application.get_candles import (
    InvalidMarketDataSymbol,
)
from stock_market_analyzer.modules.market_data.application.stream_candles import StreamCandles
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataDependencyError,
)


class RecordingStreamProvider:
    def __init__(
        self,
        *,
        updates: tuple[Candle, ...] = (),
        error: MarketDataDependencyError | None = None,
    ) -> None:
        self.updates = updates
        self.error = error
        self.stream_calls: list[tuple[str, Interval]] = []

    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        return []

    def iter_updates(self, symbol: str, interval: Interval) -> Generator[Candle, None, None]:
        self.stream_calls.append((symbol, interval))
        if self.error is not None:
            raise self.error
        return (update for update in self.updates)


def _candle(minute: int, close: str) -> Candle:
    price = Decimal(close)
    return Candle.create(
        timestamp=datetime(2026, 7, 24, 12, minute, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=100,
    )


def test_blank_symbol_is_rejected_before_stream_delegation() -> None:
    provider = RecordingStreamProvider()

    with pytest.raises(InvalidMarketDataSymbol, match="Symbol"):
        StreamCandles(provider).execute(" ", Interval.ONE_MINUTE)

    assert provider.stream_calls == []


def test_stream_normalizes_symbol_and_preserves_canonical_update_order() -> None:
    first = _candle(0, "210.00")
    second = _candle(1, "210.25")
    provider = RecordingStreamProvider(updates=(first, second))

    result = list(StreamCandles(provider).execute(" aapl ", Interval.FIVE_MINUTES))

    assert provider.stream_calls == [("AAPL", Interval.FIVE_MINUTES)]
    assert result == [first, second]
    assert all(isinstance(update, Candle) for update in result)
    assert result[0] is first
    assert result[1] is second


def test_stream_dependency_error_propagates() -> None:
    provider = RecordingStreamProvider(error=MarketDataDependencyError("stream unavailable"))

    with pytest.raises(MarketDataDependencyError, match="stream unavailable"):
        StreamCandles(provider).execute("AAPL", Interval.ONE_MINUTE)


def test_bounded_stream_close_does_not_create_extra_provider_calls() -> None:
    first = _candle(0, "210.00")
    second = _candle(1, "210.25")
    provider = RecordingStreamProvider(updates=(first, second))
    stream = cast(
        Generator[Candle, None, None],
        StreamCandles(provider).execute("AAPL", Interval.ONE_MINUTE),
    )

    assert list(islice(stream, 1)) == [first]
    stream.close()

    assert provider.stream_calls == [("AAPL", Interval.ONE_MINUTE)]
