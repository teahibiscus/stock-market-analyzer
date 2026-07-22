from __future__ import annotations

from stock_market_analyzer.modules.instruments.domain.instrument import Instrument
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_data import (
    SEED_INSTRUMENTS,
)


class SeedInstrumentReferenceProvider:
    def __init__(self, instruments: tuple[Instrument, ...] = SEED_INSTRUMENTS) -> None:
        self._instruments = instruments

    def search(self, query: str, *, limit: int) -> list[Instrument]:
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return []
        if limit < 1:
            raise ValueError("Search limit must be positive.")

        matches = [
            instrument
            for instrument in self._instruments
            if normalized_query in instrument.symbol.casefold()
            or normalized_query in instrument.company_name.casefold()
        ]
        matches.sort(key=lambda instrument: self._rank(instrument, normalized_query))
        return matches[:limit]

    @staticmethod
    def _rank(instrument: Instrument, query: str) -> tuple[int, str, str]:
        symbol = instrument.symbol.casefold()
        company_name = instrument.company_name.casefold()
        if symbol == query:
            rank = 0
        elif symbol.startswith(query):
            rank = 1
        elif company_name.startswith(query):
            rank = 2
        else:
            rank = 3
        return (rank, symbol, company_name)
