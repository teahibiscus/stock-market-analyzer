"""Create canonical raw OHLCV bar storage."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0002"
down_revision: str | None = "20260721_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS market_data"))
    op.create_table(
        "raw_ohlcv_bars",
        sa.Column("instrument_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("interval", sa.String(length=8), nullable=False),
        sa.Column("bar_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=False),
        sa.Column("high", sa.Numeric(18, 6), nullable=False),
        sa.Column("low", sa.Numeric(18, 6), nullable=False),
        sa.Column("close", sa.Numeric(18, 6), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("data_source", sa.String(length=64), nullable=False),
        sa.Column("adjustment_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("provider_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint(
            "instrument_id",
            "interval",
            "bar_timestamp",
            name="pk_raw_ohlcv_bars",
        ),
        schema="market_data",
    )
    op.create_index(
        "ix_raw_ohlcv_bars_instrument_interval_timestamp_desc",
        "raw_ohlcv_bars",
        ["instrument_id", "interval", sa.text("bar_timestamp DESC")],
        schema="market_data",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_raw_ohlcv_bars_instrument_interval_timestamp_desc",
        table_name="raw_ohlcv_bars",
        schema="market_data",
    )
    op.drop_table("raw_ohlcv_bars", schema="market_data")
    op.execute(sa.text("DROP SCHEMA IF EXISTS market_data"))
