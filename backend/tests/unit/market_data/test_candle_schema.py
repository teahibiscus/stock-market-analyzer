from sqlalchemy import create_mock_engine

from stock_market_analyzer.modules.market_data.infrastructure.persistence.models import (
    MarketDataBase,
)


def test_raw_ohlcv_schema_has_canonical_identity_and_market_fields() -> None:
    table = MarketDataBase.metadata.tables["market_data.raw_ohlcv_bars"]

    assert set(table.primary_key.columns.keys()) == {
        "instrument_id",
        "interval",
        "bar_timestamp",
    }
    assert {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "data_source",
        "adjustment_version",
        "provider_timestamp",
        "ingested_at",
    }.issubset(table.columns.keys())
    assert any("timestamp_desc" in (index.name or "") for index in table.indexes)


def test_raw_ohlcv_schema_compiles_for_postgresql_with_descending_index() -> None:
    statements: list[str] = []

    def record(sql: object, *args: object, **kwargs: object) -> None:
        statements.append(str(sql))

    engine = create_mock_engine("postgresql+psycopg://", record)
    MarketDataBase.metadata.create_all(engine)

    assert any("CREATE TABLE market_data.raw_ohlcv_bars" in item for item in statements)
    assert any("bar_timestamp DESC" in item for item in statements)
