from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval
from stock_market_analyzer.modules.market_data.infrastructure.persistence.models import (
    RawOhlcvBarModel,
)
from stock_market_analyzer.modules.market_data.ports.market_data_provider import (
    MarketDataPersistenceError,
)


class SqlAlchemyCandleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_range(
        self,
        instrument_id: str,
        interval: Interval,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[Candle]:
        if limit < 1:
            raise ValueError("Candle query limit must be positive.")
        statement = (
            select(RawOhlcvBarModel)
            .where(
                RawOhlcvBarModel.instrument_id == instrument_id,
                RawOhlcvBarModel.interval == interval.value,
                RawOhlcvBarModel.bar_timestamp >= start,
                RawOhlcvBarModel.bar_timestamp <= end,
            )
            .order_by(RawOhlcvBarModel.bar_timestamp)
            .limit(limit)
        )
        try:
            rows = self._session.scalars(statement).all()
        except SQLAlchemyError as exc:
            raise MarketDataPersistenceError("Candle persistence query failed.") from exc
        return [
            Candle.create(
                timestamp=_as_utc(row.bar_timestamp),
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
            )
            for row in rows
        ]

    def upsert(
        self,
        instrument_id: str,
        interval: Interval,
        candles: list[Candle],
        *,
        data_source: str,
        adjustment_version: int = 1,
    ) -> int:
        try:
            for candle in candles:
                self._session.merge(
                    RawOhlcvBarModel(
                        instrument_id=instrument_id,
                        interval=interval.value,
                        bar_timestamp=candle.timestamp,
                        open=candle.open,
                        high=candle.high,
                        low=candle.low,
                        close=candle.close,
                        volume=candle.volume,
                        data_source=data_source,
                        adjustment_version=adjustment_version,
                        provider_timestamp=candle.timestamp,
                    )
                )
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise MarketDataPersistenceError("Candle persistence write failed.") from exc
        return len(candles)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
