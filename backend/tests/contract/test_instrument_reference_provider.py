from __future__ import annotations

from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_provider import (
    SeedInstrumentReferenceProvider,
)
from stock_market_analyzer.modules.instruments.ports.instrument_reference_provider import (
    InstrumentReferenceProvider,
)


def test_seed_adapter_satisfies_provider_contract() -> None:
    provider = SeedInstrumentReferenceProvider()

    assert isinstance(provider, InstrumentReferenceProvider)


def test_seed_adapter_matches_symbol_and_company_case_insensitively() -> None:
    provider = SeedInstrumentReferenceProvider()

    symbol_matches = provider.search("aapl", limit=10)
    company_matches = provider.search("micro", limit=10)

    assert [item.symbol for item in symbol_matches] == ["AAPL"]
    assert [item.symbol for item in company_matches] == ["MSFT"]


def test_seed_adapter_ranks_exact_symbol_first_and_applies_limit() -> None:
    provider = SeedInstrumentReferenceProvider()

    matches = provider.search("A", limit=2)

    assert len(matches) == 2
    assert matches[0].symbol == "A"
