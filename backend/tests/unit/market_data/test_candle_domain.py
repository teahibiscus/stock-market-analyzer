from datetime import UTC, datetime
from decimal import Decimal

import pytest

from stock_market_analyzer.modules.market_data.domain.candle import Candle


def test_candle_preserves_decimal_prices_exactly() -> None:
    candle = Candle.create(
        timestamp=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
        open=Decimal("213.0100"),
        high=Decimal("213.1200"),
        low=Decimal("212.9900"),
        close=Decimal("213.0750"),
        volume=1_250,
    )

    assert candle.open == Decimal("213.0100")
    assert candle.close == Decimal("213.0750")
    assert isinstance(candle.close, Decimal)


def test_candle_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="UTC"):
        Candle.create(
            timestamp=datetime(2026, 7, 24, 12, 0),
            open=Decimal("213.00"),
            high=Decimal("214.00"),
            low=Decimal("212.00"),
            close=Decimal("213.50"),
            volume=100,
        )


def test_candle_rejects_invalid_price_range() -> None:
    with pytest.raises(ValueError, match="High"):
        Candle.create(
            timestamp=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
            open=Decimal("213.00"),
            high=Decimal("211.00"),
            low=Decimal("212.00"),
            close=Decimal("212.50"),
            volume=100,
        )


def test_candle_rejects_negative_volume() -> None:
    with pytest.raises(ValueError, match="Volume"):
        Candle.create(
            timestamp=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
            open=Decimal("213.00"),
            high=Decimal("214.00"),
            low=Decimal("212.00"),
            close=Decimal("213.50"),
            volume=-1,
        )
