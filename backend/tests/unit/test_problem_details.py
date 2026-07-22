from __future__ import annotations

from stock_market_analyzer.shared.kernel.errors.api_error import ApiError
from stock_market_analyzer.shared.kernel.errors.problem_details import ProblemDetails


def test_problem_details_uses_rfc9457_fields() -> None:
    problem = ProblemDetails(
        type="about:blank",
        title="Dependency Error",
        status=503,
        detail="Market data provider unavailable.",
        instance="/api/v1/quotes/123",
        code="DEPENDENCY_ERROR",
        correlation_id="corr-123",
        recoverable=True,
    )

    payload = problem.to_dict()

    assert payload["type"] == "about:blank"
    assert payload["title"] == "Dependency Error"
    assert payload["status"] == 503
    assert payload["detail"] == "Market data provider unavailable."
    assert payload["instance"] == "/api/v1/quotes/123"
    assert payload["code"] == "DEPENDENCY_ERROR"
    assert payload["correlationId"] == "corr-123"
    assert payload["recoverable"] is True


def test_api_error_converts_to_problem_details() -> None:
    error = ApiError(
        code="PERMISSION_DENIED",
        message="Access denied.",
        status_code=403,
        recoverable=False,
    )

    problem = error.to_problem_details(
        correlation_id="corr-456",
        instance="/api/v1/watchlists/1",
    )

    assert problem.status == 403
    assert problem.code == "PERMISSION_DENIED"
    assert problem.recoverable is False
    assert problem.correlation_id == "corr-456"
