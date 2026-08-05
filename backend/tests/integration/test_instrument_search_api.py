from __future__ import annotations

import logging

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from stock_market_analyzer.app.composition_root.factory import create_app
from stock_market_analyzer.config.settings import Settings
from stock_market_analyzer.modules.instruments.domain.instrument import Instrument
from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentCatalogBase,
)
from stock_market_analyzer.modules.instruments.infrastructure.persistence.repository import (
    SqlAlchemyInstrumentRepository,
)
from stock_market_analyzer.modules.instruments.infrastructure.persistence.seed import (
    seed_instrument_catalog,
)
from stock_market_analyzer.modules.instruments.infrastructure.reference.seed_provider import (
    SeedInstrumentReferenceProvider,
)
from stock_market_analyzer.modules.instruments.ports.instrument_reference_provider import (
    InstrumentReferencePersistenceError,
    InstrumentReferenceProvider,
)


class FailingProvider:
    def search(self, query: str, *, limit: int) -> list[Instrument]:
        raise InstrumentReferencePersistenceError("database unavailable")


def _client(
    provider: InstrumentReferenceProvider | None = None,
    *,
    result_limit: int = 20,
) -> TestClient:
    app = create_app(
        settings=Settings(instrument_search_limit=result_limit),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=provider or SeedInstrumentReferenceProvider(),
    )
    return TestClient(app)


def test_search_endpoint_returns_matching_instrument_and_success_metadata() -> None:
    response = _client().get(
        "/api/v1/instruments/search",
        params={"q": " apple "},
        headers={"X-Correlation-ID": "search-success"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "search-success"
    assert response.json() == {
        "items": [
            {
                "instrumentId": "00000000-0000-4000-8000-000000000001",
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "exchange": "NASDAQ",
                "assetType": "EQUITY",
                "status": "ACTIVE",
            }
        ],
        "metadata": {
            "state": "SUCCESS",
            "code": "INSTRUMENT_SEARCH_SUCCESS",
            "recoverable": False,
            "retryAfterSeconds": None,
            "freshness": None,
            "warnings": [],
        },
    }


def test_search_endpoint_returns_empty_state_for_no_matches() -> None:
    response = _client().get("/api/v1/instruments/search", params={"q": "no-such-company"})

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["metadata"] == {
        "state": "EMPTY",
        "code": "INSTRUMENT_SEARCH_EMPTY",
        "recoverable": True,
        "retryAfterSeconds": None,
        "freshness": None,
        "warnings": [],
    }


def test_search_endpoint_rejects_blank_query_as_problem_details() -> None:
    response = _client().get("/api/v1/instruments/search", params={"q": "   "})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["recoverable"] is True
    assert response.json()["errors"][0]["loc"][-1] == "q"


def test_search_endpoint_maps_persistence_failure_to_recoverable_problem_details() -> None:
    response = _client(FailingProvider()).get(
        "/api/v1/instruments/search",
        params={"q": "AAPL"},
        headers={"X-Correlation-ID": "search-failure"},
    )

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json() == {
        "type": "about:blank",
        "title": "Persistence Error",
        "status": 503,
        "detail": "Instrument search is temporarily unavailable.",
        "instance": "/api/v1/instruments/search",
        "code": "PERSISTENCE_ERROR",
        "correlationId": "search-failure",
        "recoverable": True,
    }


def test_search_endpoint_uses_configured_result_limit() -> None:
    response = _client(result_limit=2).get("/api/v1/instruments/search", params={"q": "a"})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_search_endpoint_reads_from_database_backed_repository() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS instruments")
        InstrumentCatalogBase.metadata.create_all(connection)

    with Session(engine) as session:
        seed_instrument_catalog(session)
        response = _client(SqlAlchemyInstrumentRepository(session)).get(
            "/api/v1/instruments/search",
            params={"q": "Microsoft"},
        )

    assert response.status_code == 200
    assert [item["symbol"] for item in response.json()["items"]] == ["MSFT"]


def test_search_endpoint_logs_completion_without_query_text() -> None:
    client = _client()
    search_logger = logging.getLogger("stock_market_analyzer.instruments.search")
    records: list[logging.LogRecord] = []

    class RecordingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = RecordingHandler()
    search_logger.addHandler(handler)
    search_logger.setLevel(logging.INFO)
    try:
        response = client.get(
            "/api/v1/instruments/search",
            params={"q": "Apple"},
            headers={"X-Correlation-ID": "telemetry-search"},
        )
    finally:
        search_logger.removeHandler(handler)

    assert response.status_code == 200
    completion_records = [
        record for record in records if record.getMessage() == "instrument_search_completed"
    ]
    assert len(completion_records) == 1
    record = completion_records[0]
    assert record.__dict__["correlation_id"] == "telemetry-search"
    assert record.__dict__["result_count"] == 1
    assert record.__dict__["application_state"] == "SUCCESS"
    assert record.__dict__["duration_ms"] >= 0
    assert "Apple" not in record.getMessage()


def test_search_endpoint_allows_configured_frontend_origin() -> None:
    app = create_app(
        settings=Settings(
            frontend_origin="http://127.0.0.1:3000",
            frontend_additional_origin="http://localhost:3000",
        ),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
    )

    response = TestClient(app).options(
        "/api/v1/instruments/search",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://127.0.0.1:3000",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_search_endpoint_allows_additional_frontend_origin() -> None:
    app = create_app(
        settings=Settings(
            frontend_origin="http://127.0.0.1:3000",
            frontend_additional_origin="http://localhost:3000",
        ),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
    )

    response = TestClient(app).options(
        "/api/v1/instruments/search",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_search_endpoint_rejects_unconfigured_frontend_origin() -> None:
    app = create_app(
        settings=Settings(
            frontend_origin="http://127.0.0.1:3000",
            frontend_additional_origin="http://localhost:3000",
        ),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
    )

    response = TestClient(app).options(
        "/api/v1/instruments/search",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://malicious.example",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_market_data_stream_preflight_allows_get_from_localhost() -> None:
    app = create_app(
        settings=Settings(
            frontend_origin="http://127.0.0.1:3000",
            frontend_additional_origin="http://localhost:3000",
        ),
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
        instrument_reference_provider=SeedInstrumentReferenceProvider(),
    )

    response = TestClient(app).options(
        "/api/v1/market-data/stream",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "GET" in response.headers["access-control-allow-methods"]
