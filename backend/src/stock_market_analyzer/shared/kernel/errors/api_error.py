from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from stock_market_analyzer.shared.kernel.errors.problem_details import ProblemDetails

ERROR_TITLES: dict[str, str] = {
    "VALIDATION_ERROR": "Validation Error",
    "PERMISSION_DENIED": "Permission Denied",
    "TIMEOUT": "Timeout",
    "DEPENDENCY_ERROR": "Dependency Error",
    "PERSISTENCE_ERROR": "Persistence Error",
    "UNAVAILABLE": "Unavailable",
}


@dataclass(slots=True)
class ApiError(Exception):
    code: str
    message: str
    status_code: int
    recoverable: bool
    extensions: dict[str, Any] | None = None

    def to_problem_details(
        self,
        *,
        correlation_id: str,
        instance: str,
    ) -> ProblemDetails:
        return ProblemDetails(
            type="about:blank",
            title=ERROR_TITLES.get(self.code, "Application Error"),
            status=self.status_code,
            detail=self.message,
            instance=instance,
            code=self.code,
            correlation_id=correlation_id,
            recoverable=self.recoverable,
            extensions=self.extensions,
        )
