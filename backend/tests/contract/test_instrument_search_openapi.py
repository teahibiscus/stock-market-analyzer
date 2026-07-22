from __future__ import annotations

from stock_market_analyzer.app.composition_root.factory import create_app
from stock_market_analyzer.config.settings import Settings
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_provider import (
    SeedInstrumentReferenceProvider,
)


def test_instrument_search_openapi_contract_is_stable_and_documented() -> None:
    app = create_app(
        settings=Settings(),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
    )

    operation = app.openapi()["paths"]["/api/v1/instruments/search"]["get"]

    assert operation["operationId"] == "searchInstruments"
    assert operation["summary"] == "Search instruments"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "InstrumentSearchResponse"
    )
    query_parameter = next(
        parameter for parameter in operation["parameters"] if parameter["name"] == "q"
    )
    assert query_parameter["required"] is True
    assert query_parameter["schema"]["maxLength"] == 100
    assert "symbol or company name" in query_parameter["description"].lower()
