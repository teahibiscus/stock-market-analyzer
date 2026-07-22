"""Create the instrument catalog schema and deterministic reference seed."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260721_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXCHANGE_SEED = [
    {
        "code": "NASDAQ",
        "name": "Nasdaq Stock Market",
        "mic_code": "XNAS",
        "timezone": "America/New_York",
    },
    {
        "code": "NYSE",
        "name": "New York Stock Exchange",
        "mic_code": "XNYS",
        "timezone": "America/New_York",
    },
    {
        "code": "NYSEARCA",
        "name": "NYSE Arca",
        "mic_code": "ARCX",
        "timezone": "America/New_York",
    },
]

INSTRUMENT_SEED = [
    {
        "id": "00000000-0000-4000-8000-000000000001",
        "company_name": "Apple Inc.",
        "asset_type": "EQUITY",
        "status": "ACTIVE",
        "primary_exchange_code": "NASDAQ",
    },
    {
        "id": "00000000-0000-4000-8000-000000000002",
        "company_name": "Microsoft Corporation",
        "asset_type": "EQUITY",
        "status": "ACTIVE",
        "primary_exchange_code": "NASDAQ",
    },
    {
        "id": "00000000-0000-4000-8000-000000000003",
        "company_name": "Alphabet Inc.",
        "asset_type": "EQUITY",
        "status": "ACTIVE",
        "primary_exchange_code": "NASDAQ",
    },
    {
        "id": "00000000-0000-4000-8000-000000000004",
        "company_name": "Amazon.com, Inc.",
        "asset_type": "EQUITY",
        "status": "ACTIVE",
        "primary_exchange_code": "NASDAQ",
    },
    {
        "id": "00000000-0000-4000-8000-000000000005",
        "company_name": "Agilent Technologies, Inc.",
        "asset_type": "EQUITY",
        "status": "ACTIVE",
        "primary_exchange_code": "NYSE",
    },
    {
        "id": "00000000-0000-4000-8000-000000000006",
        "company_name": "SPDR S&P 500 ETF Trust",
        "asset_type": "ETF",
        "status": "ACTIVE",
        "primary_exchange_code": "NYSEARCA",
    },
]

INSTRUMENT_SYMBOL_SEED = [
    {
        "instrument_id": instrument["id"],
        "exchange_code": instrument["primary_exchange_code"],
        "symbol": symbol,
        "is_primary": True,
    }
    for instrument, symbol in zip(
        INSTRUMENT_SEED,
        ("AAPL", "MSFT", "GOOGL", "AMZN", "A", "SPY"),
        strict=True,
    )
]


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS instruments"))

    exchanges = op.create_table(
        "exchanges",
        sa.Column("code", sa.String(length=16), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("mic_code", sa.String(length=4), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("mic_code", name="uq_exchanges_mic_code"),
        schema="instruments",
    )
    instruments = op.create_table(
        "instruments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("primary_exchange_code", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "asset_type IN ('EQUITY', 'ETF')",
            name="ck_instruments_asset_type_supported",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_instruments_status_supported",
        ),
        sa.ForeignKeyConstraint(
            ["primary_exchange_code"],
            ["instruments.exchanges.code"],
            name="fk_instruments_primary_exchange_code_exchanges",
        ),
        schema="instruments",
    )
    instrument_symbols = op.create_table(
        "instrument_symbols",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("instrument_id", sa.String(length=36), nullable=False),
        sa.Column("exchange_code", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.instruments.id"],
            name="fk_instrument_symbols_instrument_id_instruments",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["exchange_code"],
            ["instruments.exchanges.code"],
            name="fk_instrument_symbols_exchange_code_exchanges",
        ),
        schema="instruments",
    )

    op.create_index(
        "ix_instruments_company_name",
        "instruments",
        ["company_name"],
        schema="instruments",
    )
    op.create_index(
        "ix_instrument_symbols_symbol",
        "instrument_symbols",
        ["symbol"],
        schema="instruments",
    )
    op.create_index(
        "uq_instrument_symbols_exchange_symbol",
        "instrument_symbols",
        ["exchange_code", "symbol"],
        unique=True,
        schema="instruments",
    )

    op.bulk_insert(exchanges, EXCHANGE_SEED)
    op.bulk_insert(instruments, INSTRUMENT_SEED)
    op.bulk_insert(instrument_symbols, INSTRUMENT_SYMBOL_SEED)


def downgrade() -> None:
    op.drop_table("instrument_symbols", schema="instruments")
    op.drop_table("instruments", schema="instruments")
    op.drop_table("exchanges", schema="instruments")
    op.execute(sa.text("DROP SCHEMA IF EXISTS instruments"))
