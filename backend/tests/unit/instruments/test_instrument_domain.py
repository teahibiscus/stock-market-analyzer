from __future__ import annotations

import pytest

from stock_market_analyzer.modules.instruments.domain.instrument import (
    AssetType,
    Instrument,
    InstrumentStatus,
)


def test_instrument_normalizes_reference_data() -> None:
    instrument = Instrument.create(
        instrument_id="  9f0f7397-e0f2-4e96-aa8f-3ab751e78b9a  ",
        symbol=" aapl ",
        company_name=" Apple Inc. ",
        exchange_code=" nasdaq ",
        asset_type=AssetType.EQUITY,
        status=InstrumentStatus.ACTIVE,
    )

    assert instrument.instrument_id == "9f0f7397-e0f2-4e96-aa8f-3ab751e78b9a"
    assert instrument.symbol == "AAPL"
    assert instrument.company_name == "Apple Inc."
    assert instrument.exchange_code == "NASDAQ"


@pytest.mark.parametrize("field", ["symbol", "company_name", "exchange_code"])
def test_instrument_rejects_missing_required_reference_data(field: str) -> None:
    values = {
        "instrument_id": "9f0f7397-e0f2-4e96-aa8f-3ab751e78b9a",
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "exchange_code": "NASDAQ",
        "asset_type": AssetType.EQUITY,
        "status": InstrumentStatus.ACTIVE,
    }
    values[field] = " "

    with pytest.raises(ValueError, match="must not be empty"):
        Instrument.create(**values)  # type: ignore[arg-type]
