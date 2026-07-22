from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from stock_market_analyzer.shared.kernel.identifiers.instrument_id import (
    InstrumentId,
    parse_instrument_id,
)


class AssetType(StrEnum):
    EQUITY = "EQUITY"
    ETF = "ETF"


class InstrumentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


def _required(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    return normalized


@dataclass(frozen=True, slots=True)
class Instrument:
    instrument_id: InstrumentId
    symbol: str
    company_name: str
    exchange_code: str
    asset_type: AssetType
    status: InstrumentStatus

    @classmethod
    def create(
        cls,
        *,
        instrument_id: str,
        symbol: str,
        company_name: str,
        exchange_code: str,
        asset_type: AssetType,
        status: InstrumentStatus,
    ) -> Instrument:
        return cls(
            instrument_id=parse_instrument_id(instrument_id),
            symbol=_required(symbol, "Symbol").upper(),
            company_name=_required(company_name, "Company name"),
            exchange_code=_required(exchange_code, "Exchange code").upper(),
            asset_type=asset_type,
            status=status,
        )
