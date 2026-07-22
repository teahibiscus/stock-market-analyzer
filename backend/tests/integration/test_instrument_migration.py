from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from sqlalchemy import create_mock_engine

from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentModel,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    BACKEND_ROOT / "migrations" / "versions" / "20260721_0001_create_instrument_catalog.py"
)


def _load_migration() -> ModuleType:
    specification = importlib.util.spec_from_file_location("instrument_migration", MIGRATION_PATH)
    assert specification is not None
    assert specification.loader is not None
    migration = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(migration)
    return migration


def test_instrument_catalog_migration_is_reversible_and_seeds_reference_data() -> None:
    migration = _load_migration()

    assert migration.revision == "20260721_0001"
    assert migration.down_revision is None
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)
    assert {row["symbol"] for row in migration.INSTRUMENT_SYMBOL_SEED} >= {
        "AAPL",
        "MSFT",
        "GOOGL",
    }


def test_instrument_catalog_metadata_compiles_for_postgresql() -> None:
    statements: list[str] = []
    engine = create_mock_engine(
        "postgresql+psycopg://",
        lambda sql, *args, **kwargs: statements.append(str(sql)),
    )

    InstrumentModel.metadata.create_all(engine)

    assert engine.dialect.name == "postgresql"
    assert any("CREATE TABLE instruments.instruments" in statement for statement in statements)
