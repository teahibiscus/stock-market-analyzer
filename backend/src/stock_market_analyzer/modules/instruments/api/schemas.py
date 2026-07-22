from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from stock_market_analyzer.modules.application_state.domain.enums import ApplicationState
from stock_market_analyzer.modules.application_state.domain.metadata import (
    ApplicationStateMetadata,
)
from stock_market_analyzer.modules.instruments.domain.instrument import (
    AssetType,
    Instrument,
    InstrumentStatus,
)


class InstrumentSearchItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    instrument_id: str = Field(serialization_alias="instrumentId")
    symbol: str
    company_name: str = Field(serialization_alias="companyName")
    exchange: str
    asset_type: AssetType = Field(serialization_alias="assetType")
    status: InstrumentStatus

    @classmethod
    def from_domain(cls, instrument: Instrument) -> InstrumentSearchItem:
        return cls(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            company_name=instrument.company_name,
            exchange=instrument.exchange_code,
            asset_type=instrument.asset_type,
            status=instrument.status,
        )


class InstrumentSearchResponse(BaseModel):
    items: list[InstrumentSearchItem]
    metadata: ApplicationStateMetadata

    @classmethod
    def from_results(cls, instruments: list[Instrument]) -> InstrumentSearchResponse:
        has_results = bool(instruments)
        return cls(
            items=[InstrumentSearchItem.from_domain(instrument) for instrument in instruments],
            metadata=ApplicationStateMetadata(
                state=ApplicationState.SUCCESS if has_results else ApplicationState.EMPTY,
                code=("INSTRUMENT_SEARCH_SUCCESS" if has_results else "INSTRUMENT_SEARCH_EMPTY"),
                recoverable=not has_results,
            ),
        )
