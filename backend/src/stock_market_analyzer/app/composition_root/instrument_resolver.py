from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentModel,
    InstrumentSymbolModel,
)
from stock_market_analyzer.modules.market_data.ports.instrument_resolver import (
    InstrumentNotFoundError,
    ResolvedInstrument,
)


class SqlAlchemyInstrumentResolver:
    """Composition adapter bridging market data to the instrument catalog."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def resolve(self, instrument_id: str) -> ResolvedInstrument:
        statement = (
            select(InstrumentModel.id, InstrumentSymbolModel.symbol)
            .join(
                InstrumentSymbolModel,
                InstrumentSymbolModel.instrument_id == InstrumentModel.id,
            )
            .where(
                InstrumentModel.id == instrument_id,
                InstrumentModel.status == "ACTIVE",
                InstrumentSymbolModel.is_primary.is_(True),
            )
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            raise InstrumentNotFoundError("Instrument is not supported.")
        return ResolvedInstrument(instrument_id=row.id, symbol=row.symbol)
