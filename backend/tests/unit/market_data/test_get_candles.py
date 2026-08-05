from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from stock_market_analyzer.modules.market_data.application.get_candles import (
    GetCandles,
    InvalidMarketDataSymbol,
    UnsupportedCandleCombination,
)
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataDependencyError,
    MarketDataProviderError,
    SymbolNotSupportedError,
)


class RecordingProvider:
    def __init__(
        self,
        *,
        candles: list[Candle] | None = None,
        error: MarketDataProviderError | None = None,
    ) -> None:
        self.candles = candles or []
        self.error = error
        self.history_calls: list[tuple[str, Interval, Period]] = []

    def get_candles(
        self,
        symbol: str,
        interval: Interval,
        period: Period,
    ) -> list[Candle]:
        self.history_calls.append((symbol, interval, period))
        if self.error is not None:
            raise self.error
        return self.candles

    def iter_updates(self, symbol: str, interval: Interval) -> Iterator[Candle]:
        return iter(())


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


def test_blank_symbol_is_rejected_before_provider_delegation() -> None:
    provider = RecordingProvider()

    with pytest.raises(InvalidMarketDataSymbol, match="Symbol"):
        GetCandles(provider).execute("   ", Interval.ONE_MINUTE, Period.ONE_DAY)

    assert provider.history_calls == []


def test_valid_request_is_normalized_and_preserves_candle_order_and_identity() -> None:
    first = _candle(0, "210.00")
    second = _candle(1, "210.25")
    provider = RecordingProvider(candles=[first, second])

    result = GetCandles(provider).execute(
        "  aapl  ",
        Interval.ONE_MINUTE,
        Period.ONE_DAY,
    )

    assert provider.history_calls == [
        ("AAPL", Interval.ONE_MINUTE, Period.ONE_DAY),
    ]
    assert result == [first, second]
    assert result[0] is first
    assert result[1] is second


def test_unsupported_combination_is_rejected_before_provider_delegation() -> None:
    provider = RecordingProvider()

    with pytest.raises(UnsupportedCandleCombination, match=r"1m.*1mo"):
        GetCandles(provider).execute("AAPL", Interval.ONE_MINUTE, Period.ONE_MONTH)

    assert provider.history_calls == []


def test_empty_provider_result_is_preserved() -> None:
    provider = RecordingProvider()

    result = GetCandles(provider).execute("AAPL", Interval.ONE_DAY, Period.ONE_MONTH)

    assert result == []


def test_symbol_not_supported_error_propagates() -> None:
    provider = RecordingProvider(error=SymbolNotSupportedError("unsupported"))

    with pytest.raises(SymbolNotSupportedError, match="unsupported"):
        GetCandles(provider).execute("MSFT", Interval.ONE_DAY, Period.ONE_MONTH)


def test_dependency_error_propagates() -> None:
    provider = RecordingProvider(error=MarketDataDependencyError("provider unavailable"))

    with pytest.raises(MarketDataDependencyError, match="provider unavailable"):
        GetCandles(provider).execute("AAPL", Interval.ONE_DAY, Period.ONE_MONTH)
