from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentCatalogBase,
)
from stock_market_analyzer.modules.instruments.infrastructure.persistence.repository import (
    SqlAlchemyInstrumentRepository,
)
from stock_market_analyzer.modules.instruments.infrastructure.persistence.seed import (
    seed_instrument_catalog,
)


def test_repository_searches_seeded_instruments_by_symbol_and_company() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS instruments")
        InstrumentCatalogBase.metadata.create_all(connection)

    with Session(engine) as session:
        seed_instrument_catalog(session)
        repository = SqlAlchemyInstrumentRepository(session)

        assert [item.symbol for item in repository.search("aapl", limit=10)] == ["AAPL"]
        assert [item.symbol for item in repository.search("micro", limit=10)] == ["MSFT"]


def test_seed_operation_is_idempotent() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS instruments")
        InstrumentCatalogBase.metadata.create_all(connection)

    with Session(engine) as session:
        seed_instrument_catalog(session)
        seed_instrument_catalog(session)

        assert len(SqlAlchemyInstrumentRepository(session).search("a", limit=100)) == 5
