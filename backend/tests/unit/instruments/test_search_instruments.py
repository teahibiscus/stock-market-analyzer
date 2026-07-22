from __future__ import annotations

import pytest

from stock_market_analyzer.modules.instruments.application.search_instruments import (
    InvalidInstrumentSearchQuery,
    SearchInstruments,
)
from stock_market_analyzer.modules.instruments.domain.instrument import Instrument
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_provider import (
    SeedInstrumentReferenceProvider,
)


class RecordingProvider:
    def __init__(self, results: list[Instrument]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, *, limit: int) -> list[Instrument]:
        self.calls.append((query, limit))
        return self.results[:limit]


def test_search_use_case_trims_query_and_applies_configured_limit() -> None:
    seeded = SeedInstrumentReferenceProvider().search("a", limit=10)
    provider = RecordingProvider(seeded)
    use_case = SearchInstruments(provider=provider, result_limit=2)

    result = use_case.execute("  a  ")

    assert provider.calls == [("a", 2)]
    assert len(result) == 2


@pytest.mark.parametrize("query", ["", " ", "\t\r\n"])
def test_search_use_case_rejects_query_empty_after_trimming(query: str) -> None:
    use_case = SearchInstruments(
        provider=RecordingProvider([]),
        result_limit=10,
    )

    with pytest.raises(InvalidInstrumentSearchQuery):
        use_case.execute(query)
