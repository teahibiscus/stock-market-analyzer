from __future__ import annotations

from dataclasses import dataclass

from stock_market_analyzer.modules.instruments.domain.instrument import Instrument
from stock_market_analyzer.modules.instruments.ports.instrument_reference_provider import (
    InstrumentReferenceProvider,
)


class InvalidInstrumentSearchQuery(ValueError):
    """The query contains no searchable characters after normalization."""


@dataclass(frozen=True, slots=True)
class SearchInstruments:
    provider: InstrumentReferenceProvider
    result_limit: int

    def __post_init__(self) -> None:
        if self.result_limit < 1:
            raise ValueError("Instrument search result limit must be positive.")

    def execute(self, query: str) -> list[Instrument]:
        normalized_query = query.strip()
        if not normalized_query:
            raise InvalidInstrumentSearchQuery("Search query must not be empty.")
        return self.provider.search(normalized_query, limit=self.result_limit)
