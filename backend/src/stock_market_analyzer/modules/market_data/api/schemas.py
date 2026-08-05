from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from stock_market_analyzer.modules.application_state.domain.enums import (
    ApplicationState,
    FreshnessState,
)
from stock_market_analyzer.modules.application_state.domain.metadata import (
    ApplicationStateMetadata,
    FreshnessMetadata,
)
from stock_market_analyzer.modules.market_data.domain.candle import Candle
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period

DEMO_DATA_WARNING = "SYNTHETIC_MARKET_DATA"
READ_THROUGH_WARNING = "MARKET_DATA_READ_THROUGH"


class CandleSchema(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    @classmethod
    def from_domain(cls, candle: Candle) -> CandleSchema:
        return cls(
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )


class CandleSeriesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    instrument_id: str | None = Field(default=None, serialization_alias="instrumentId")
    symbol: str
    interval: Interval
    period: Period
    timezone: Literal["UTC"] = "UTC"
    data_source: str = Field(serialization_alias="dataSource")
    adjustment_mode: Literal["RAW"] = Field(default="RAW", serialization_alias="adjustmentMode")
    adjustment_version: int = Field(default=1, serialization_alias="adjustmentVersion")
    schema_version: int = Field(default=1, serialization_alias="schemaVersion")
    as_of: datetime = Field(serialization_alias="asOf")
    candles: list[CandleSchema]
    metadata: ApplicationStateMetadata

    @classmethod
    def from_candles(
        cls,
        *,
        symbol: str,
        interval: Interval,
        period: Period,
        data_source: str,
        as_of: datetime,
        candles: list[Candle],
        instrument_id: str | None = None,
        read_through: bool = False,
    ) -> CandleSeriesResponse:
        has_candles = bool(candles)
        is_demo = data_source.casefold() == "demo"
        provider_timestamp = candles[-1].timestamp if candles else None
        warnings = [DEMO_DATA_WARNING] if is_demo else []
        if read_through:
            warnings.append(READ_THROUGH_WARNING)
        return cls(
            instrument_id=instrument_id,
            symbol=symbol,
            interval=interval,
            period=period,
            data_source=data_source,
            as_of=as_of,
            candles=[CandleSchema.from_domain(candle) for candle in candles],
            metadata=ApplicationStateMetadata(
                state=ApplicationState.SUCCESS if has_candles else ApplicationState.EMPTY,
                code=(
                    "MARKET_DATA_CANDLES_SUCCESS" if has_candles else "MARKET_DATA_CANDLES_EMPTY"
                ),
                recoverable=not has_candles,
                freshness=FreshnessMetadata(
                    provider_timestamp=provider_timestamp,
                    ingested_at=as_of,
                    delay_seconds=(
                        max(0, int((as_of - provider_timestamp).total_seconds()))
                        if provider_timestamp is not None
                        else None
                    ),
                    state=FreshnessState.STALE if is_demo else FreshnessState.FRESH,
                ),
                warnings=warnings,
            ),
        )


class StreamCandleUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    interval: Interval
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    event_timestamp: datetime = Field(serialization_alias="eventTimestamp")
    sequence: int = Field(ge=1)

    @classmethod
    def from_candle(
        cls,
        *,
        symbol: str,
        interval: Interval,
        candle: Candle,
        event_timestamp: datetime,
        sequence: int,
    ) -> StreamCandleUpdate:
        return cls(
            symbol=symbol,
            interval=interval,
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
            event_timestamp=event_timestamp,
            sequence=sequence,
        )
