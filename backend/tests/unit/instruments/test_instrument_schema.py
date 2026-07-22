from __future__ import annotations

from sqlalchemy import MetaData

from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentModel,
)


def test_instrument_catalog_owns_expected_tables_and_columns() -> None:
    metadata = InstrumentModel.metadata

    assert isinstance(metadata, MetaData)
    assert set(metadata.tables) >= {
        "instruments.exchanges",
        "instruments.instruments",
        "instruments.instrument_symbols",
    }
    assert set(metadata.tables["instruments.instruments"].columns.keys()) >= {
        "id",
        "company_name",
        "asset_type",
        "status",
        "primary_exchange_code",
        "created_at",
        "updated_at",
    }
    assert set(metadata.tables["instruments.instrument_symbols"].columns.keys()) >= {
        "id",
        "instrument_id",
        "exchange_code",
        "symbol",
        "is_primary",
        "created_at",
        "updated_at",
    }


def test_instrument_catalog_defines_search_and_identity_indexes() -> None:
    metadata = InstrumentModel.metadata
    index_names = {index.name for table in metadata.tables.values() for index in table.indexes}

    assert {
        "ix_instruments_company_name",
        "ix_instrument_symbols_symbol",
        "uq_instrument_symbols_exchange_symbol",
    }.issubset(index_names)
