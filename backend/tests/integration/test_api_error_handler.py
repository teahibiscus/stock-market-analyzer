from __future__ import annotations

from fastapi.testclient import TestClient

from stock_market_analyzer.app.composition_root.factory import create_app
from stock_market_analyzer.shared.kernel.errors.api_error import ApiError


def test_api_error_handler_returns_problem_details_with_correlation_id() -> None:
    app = create_app(
        database_health_checker=lambda: True,
        cache_health_checker=lambda: True,
    )

    @app.get("/test-error")
    def raise_api_error() -> None:
        raise ApiError(
            code="DEPENDENCY_ERROR",
            message="Upstream dependency unavailable.",
            status_code=503,
            recoverable=True,
        )

    client = TestClient(app)
    response = client.get("/test-error", headers={"X-Correlation-ID": "corr-integration"})

    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["X-Correlation-ID"] == "corr-integration"
    assert response.json() == {
        "type": "about:blank",
        "title": "Dependency Error",
        "status": 503,
        "detail": "Upstream dependency unavailable.",
        "instance": "/test-error",
        "code": "DEPENDENCY_ERROR",
        "correlationId": "corr-integration",
        "recoverable": True,
    }
