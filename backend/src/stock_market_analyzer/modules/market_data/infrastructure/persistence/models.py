from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Uuid,
    desc,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class MarketDataBase(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "pk": "pk_%(table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
        }
    )


class RawOhlcvBarModel(MarketDataBase):
    __tablename__ = "raw_ohlcv_bars"
    __table_args__ = (
        Index(
            "ix_raw_ohlcv_bars_instrument_interval_timestamp_desc",
            "instrument_id",
            "interval",
            desc("bar_timestamp"),
        ),
        {"schema": "market_data"},
    )

    instrument_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    interval: Mapped[str] = mapped_column(String(8), primary_key=True)
    bar_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False
    )
    data_source: Mapped[str] = mapped_column(String(64), nullable=False)
    adjustment_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    provider_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
