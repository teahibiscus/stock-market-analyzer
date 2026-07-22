from __future__ import annotations

from stock_market_analyzer.modules.instruments.domain.instrument import (
    AssetType,
    Instrument,
    InstrumentStatus,
)

SEED_INSTRUMENTS: tuple[Instrument, ...] = (
    Instrument.create(
        instrument_id="00000000-0000-4000-8000-000000000001",
        symbol="AAPL",
        company_name="Apple Inc.",
        exchange_code="NASDAQ",
        asset_type=AssetType.EQUITY,
        status=InstrumentStatus.ACTIVE,
    ),
    Instrument.create(
        instrument_id="00000000-0000-4000-8000-000000000002",
        symbol="MSFT",
        company_name="Microsoft Corporation",
        exchange_code="NASDAQ",
        asset_type=AssetType.EQUITY,
        status=InstrumentStatus.ACTIVE,
    ),
    Instrument.create(
        instrument_id="00000000-0000-4000-8000-000000000003",
        symbol="GOOGL",
        company_name="Alphabet Inc.",
        exchange_code="NASDAQ",
        asset_type=AssetType.EQUITY,
        status=InstrumentStatus.ACTIVE,
    ),
    Instrument.create(
        instrument_id="00000000-0000-4000-8000-000000000004",
        symbol="AMZN",
        company_name="Amazon.com, Inc.",
        exchange_code="NASDAQ",
        asset_type=AssetType.EQUITY,
        status=InstrumentStatus.ACTIVE,
    ),
    Instrument.create(
        instrument_id="00000000-0000-4000-8000-000000000005",
        symbol="A",
        company_name="Agilent Technologies, Inc.",
        exchange_code="NYSE",
        asset_type=AssetType.EQUITY,
        status=InstrumentStatus.ACTIVE,
    ),
    Instrument.create(
        instrument_id="00000000-0000-4000-8000-000000000006",
        symbol="SPY",
        company_name="SPDR S&P 500 ETF Trust",
        exchange_code="NYSEARCA",
        asset_type=AssetType.ETF,
        status=InstrumentStatus.ACTIVE,
    ),
)
