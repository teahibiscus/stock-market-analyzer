from __future__ import annotations

from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from stock_market_analyzer.modules.instruments.domain.instrument import (
    AssetType,
    Instrument,
    InstrumentStatus,
)
from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentModel,
    InstrumentSymbolModel,
)
from stock_market_analyzer.modules.instruments.ports.instrument_reference_provider import (
    InstrumentReferencePersistenceError,
)


class SqlAlchemyInstrumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, query: str, *, limit: int) -> list[Instrument]:
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return []
        if limit < 1:
            raise ValueError("Search limit must be positive.")

        escaped_query = (
            normalized_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        contains_pattern = f"%{escaped_query}%"
        starts_with_pattern = f"{escaped_query}%"
        normalized_symbol = func.lower(InstrumentSymbolModel.symbol)
        normalized_company_name = func.lower(InstrumentModel.company_name)
        ranking = case(
            (normalized_symbol == normalized_query, 0),
            (normalized_symbol.like(starts_with_pattern, escape="\\"), 1),
            (normalized_company_name.like(starts_with_pattern, escape="\\"), 2),
            else_=3,
        )

        statement = (
            select(InstrumentModel, InstrumentSymbolModel.symbol)
            .join(
                InstrumentSymbolModel,
                InstrumentSymbolModel.instrument_id == InstrumentModel.id,
            )
            .where(
                InstrumentSymbolModel.is_primary.is_(True),
                InstrumentModel.status == InstrumentStatus.ACTIVE.value,
                or_(
                    normalized_symbol.like(contains_pattern, escape="\\"),
                    normalized_company_name.like(contains_pattern, escape="\\"),
                ),
            )
            .order_by(ranking, normalized_symbol, normalized_company_name)
            .limit(limit)
        )

        try:
            rows = self._session.execute(statement).tuples().all()
        except SQLAlchemyError as exc:
            raise InstrumentReferencePersistenceError(
                "Instrument catalog persistence request failed."
            ) from exc

        return [
            Instrument.create(
                instrument_id=model.id,
                symbol=symbol,
                company_name=model.company_name,
                exchange_code=model.primary_exchange_code,
                asset_type=AssetType(model.asset_type),
                status=InstrumentStatus(model.status),
            )
            for model, symbol in rows
        ]
