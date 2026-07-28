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

DEMO_DATA_WARNING = "Simulated demo data; this is not live exchange market data."


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

    symbol: str
    interval: Interval
    period: Period
    timezone: Literal["UTC"] = "UTC"
    data_source: str = Field(serialization_alias="dataSource")
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
    ) -> CandleSeriesResponse:
        has_candles = bool(candles)
        return cls(
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
                    provider_timestamp=as_of,
                    ingested_at=as_of,
                    delay_seconds=0,
                    state=FreshnessState.FRESH,
                ),
                warnings=[DEMO_DATA_WARNING],
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
