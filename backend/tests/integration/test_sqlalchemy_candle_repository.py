from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval
from stock_market_analyzer.modules.market_data.infrastructure.persistence.models import (
    MarketDataBase,
)
from stock_market_analyzer.modules.market_data.infrastructure.persistence.repository import (
    SqlAlchemyCandleRepository,
)

INSTRUMENT_ID = "00000000-0000-4000-8000-000000000001"


def test_repository_upsert_is_idempotent_and_range_is_ascending() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS market_data")
        MarketDataBase.metadata.create_all(connection)

    start = datetime(2026, 7, 1, tzinfo=UTC)
    candles = [_candle(start + timedelta(days=offset)) for offset in (1, 0)]
    with Session(engine) as session:
        repository = SqlAlchemyCandleRepository(session)
        assert repository.upsert(INSTRUMENT_ID, Interval.ONE_DAY, candles, data_source="demo") == 2
        assert repository.upsert(INSTRUMENT_ID, Interval.ONE_DAY, candles, data_source="demo") == 2

        result = repository.get_range(
            INSTRUMENT_ID,
            Interval.ONE_DAY,
            start=start,
            end=start + timedelta(days=2),
            limit=10,
        )

    assert [candle.timestamp for candle in result] == [start, start + timedelta(days=1)]


def _candle(timestamp: datetime) -> Candle:
    return Candle.create(
        timestamp=timestamp,
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=1_000,
    )
