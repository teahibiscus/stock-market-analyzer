from __future__ import annotations

from stock_market_analyzer.modules.market_data.infrastructure.persistence.repository import (
    SqlAlchemyCandleRepository,
)
from stock_market_analyzer.modules.market_data.ports.candle_repository import CandleRepository


def test_sqlalchemy_repository_satisfies_candle_repository_contract() -> None:
    assert isinstance(
        SqlAlchemyCandleRepository.__new__(SqlAlchemyCandleRepository), CandleRepository
    )
