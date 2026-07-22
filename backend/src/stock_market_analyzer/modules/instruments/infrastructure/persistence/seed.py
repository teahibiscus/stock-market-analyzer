from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from stock_market_analyzer.modules.instruments.domain.instrument import Instrument
from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    ExchangeModel,
    InstrumentModel,
    InstrumentSymbolModel,
)
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_data import (
    SEED_INSTRUMENTS,
)

EXCHANGE_SEED = {
    "NASDAQ": {
        "name": "Nasdaq Stock Market",
        "mic_code": "XNAS",
        "timezone": "America/New_York",
    },
    "NYSE": {
        "name": "New York Stock Exchange",
        "mic_code": "XNYS",
        "timezone": "America/New_York",
    },
    "NYSEARCA": {
        "name": "NYSE Arca",
        "mic_code": "ARCX",
        "timezone": "America/New_York",
    },
}


def seed_instrument_catalog(
    session: Session,
    instruments: Sequence[Instrument] = SEED_INSTRUMENTS,
) -> None:
    existing_exchanges = set(session.scalars(select(ExchangeModel.code)))
    for code, values in EXCHANGE_SEED.items():
        if code not in existing_exchanges:
            session.add(ExchangeModel(code=code, **values))
    session.flush()

    existing_instrument_ids = set(session.scalars(select(InstrumentModel.id)))
    for instrument in instruments:
        if instrument.instrument_id not in existing_instrument_ids:
            session.add(
                InstrumentModel(
                    id=instrument.instrument_id,
                    company_name=instrument.company_name,
                    asset_type=instrument.asset_type.value,
                    status=instrument.status.value,
                    primary_exchange_code=instrument.exchange_code,
                )
            )
    session.flush()

    existing_symbols = set(
        session.execute(
            select(InstrumentSymbolModel.exchange_code, InstrumentSymbolModel.symbol)
        ).tuples()
    )
    for instrument in instruments:
        identity = (instrument.exchange_code, instrument.symbol)
        if identity not in existing_symbols:
            session.add(
                InstrumentSymbolModel(
                    instrument_id=instrument.instrument_id,
                    exchange_code=instrument.exchange_code,
                    symbol=instrument.symbol,
                    is_primary=True,
                )
            )
    session.flush()
