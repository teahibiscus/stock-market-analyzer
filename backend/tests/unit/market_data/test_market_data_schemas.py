from datetime import UTC, datetime
from decimal import Decimal

from stock_market_analyzer.modules.market_data.api.schemas import (
    CandleSchema,
    CandleSeriesResponse,
    StreamCandleUpdate,
)
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period


def _candle() -> Candle:
    return Candle.create(
        timestamp=datetime(2026, 7, 24, 15, 30, tzinfo=UTC),
        open=Decimal("210.0100"),
        high=Decimal("210.2500"),
        low=Decimal("209.9900"),
        close=Decimal("210.1250"),
        volume=1_234,
    )


def test_candle_schema_preserves_canonical_values_and_decimal_precision() -> None:
    schema = CandleSchema.from_domain(_candle())

    assert schema.timestamp.tzinfo is UTC
    assert schema.close == Decimal("210.1250")
    assert schema.model_dump(mode="json")["close"] == "210.1250"


def test_history_schema_serializes_aliases_success_freshness_and_demo_warning() -> None:
    as_of = datetime(2026, 7, 24, 15, 30, 5, tzinfo=UTC)

    response = CandleSeriesResponse.from_candles(
        symbol="AAPL",
        interval=Interval.ONE_MINUTE,
        period=Period.ONE_DAY,
        data_source="demo",
        as_of=as_of,
        candles=[_candle()],
    )
    payload = response.model_dump(mode="json", by_alias=True)

    assert payload["dataSource"] == "demo"
    assert payload["asOf"] == "2026-07-24T15:30:05Z"
    assert payload["timezone"] == "UTC"
    assert payload["metadata"]["state"] == "SUCCESS"
    assert payload["metadata"]["freshness"]["providerTimestamp"] == "2026-07-24T15:30:00Z"
    assert payload["metadata"]["freshness"]["state"] == "STALE"
    assert "SYNTHETIC_MARKET_DATA" in payload["metadata"]["warnings"]


def test_history_schema_represents_empty_results() -> None:
    response = CandleSeriesResponse.from_candles(
        symbol="AAPL",
        interval=Interval.ONE_DAY,
        period=Period.ONE_MONTH,
        data_source="demo",
        as_of=datetime(2026, 7, 24, tzinfo=UTC),
        candles=[],
    )

    assert response.candles == []
    assert response.metadata.state.value == "EMPTY"
    assert response.metadata.recoverable is True


def test_stream_update_converts_canonical_candle_with_sequence_and_alias() -> None:
    update = StreamCandleUpdate.from_candle(
        symbol="AAPL",
        interval=Interval.ONE_MINUTE,
        candle=_candle(),
        event_timestamp=datetime(2026, 7, 24, 15, 30, 6, tzinfo=UTC),
        sequence=7,
    )
    payload = update.model_dump(mode="json", by_alias=True)

    assert payload["symbol"] == "AAPL"
    assert payload["interval"] == "1m"
    assert payload["timestamp"] == "2026-07-24T15:30:00Z"
    assert payload["close"] == "210.1250"
    assert payload["eventTimestamp"] == "2026-07-24T15:30:06Z"
    assert payload["sequence"] == 7
