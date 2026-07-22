from __future__ import annotations

from fastapi.testclient import TestClient

from stock_market_analyzer.app.composition_root.factory import create_app


def test_correlation_id_is_generated_when_missing() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    correlation_id = response.headers.get("X-Correlation-ID")
    assert correlation_id is not None
    assert len(correlation_id) > 0


def test_correlation_id_is_echoed_when_provided() -> None:
    client = TestClient(create_app())
    expected_correlation_id = "test-correlation-123"

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": expected_correlation_id},
    )

    assert response.headers.get("X-Correlation-ID") == expected_correlation_id
