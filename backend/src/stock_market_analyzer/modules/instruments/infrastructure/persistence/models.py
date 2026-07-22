from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class InstrumentCatalogBase(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
        }
    )


class ExchangeModel(InstrumentCatalogBase):
    __tablename__ = "exchanges"
    __table_args__ = {"schema": "instruments"}  # noqa: RUF012

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    mic_code: Mapped[str] = mapped_column(String(4), nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class InstrumentModel(InstrumentCatalogBase):
    __tablename__ = "instruments"
    __table_args__ = (
        CheckConstraint(
            "asset_type IN ('EQUITY', 'ETF')",
            name="asset_type_supported",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="status_supported",
        ),
        Index("ix_instruments_company_name", "company_name"),
        {"schema": "instruments"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_exchange_code: Mapped[str] = mapped_column(
        ForeignKey("instruments.exchanges.code"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class InstrumentSymbolModel(InstrumentCatalogBase):
    __tablename__ = "instrument_symbols"
    __table_args__ = (
        Index("ix_instrument_symbols_symbol", "symbol"),
        Index(
            "uq_instrument_symbols_exchange_symbol",
            "exchange_code",
            "symbol",
            unique=True,
        ),
        {"schema": "instruments"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    instrument_id: Mapped[str] = mapped_column(
        ForeignKey("instruments.instruments.id", ondelete="CASCADE"), nullable=False
    )
    exchange_code: Mapped[str] = mapped_column(
        ForeignKey("instruments.exchanges.code"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
