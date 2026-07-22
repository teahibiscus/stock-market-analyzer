from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from stock_market_analyzer.shared.kernel.errors.api_error import ApiError

ExceptionHandler = Callable[[Request, Exception], Response | Awaitable[Response]]


def _problem_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    title: str,
    detail: str,
    recoverable: bool,
    extensions: dict[str, object] | None = None,
) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "")
    headers = {"X-Correlation-ID": correlation_id} if correlation_id else None

    return JSONResponse(
        status_code=status_code,
        media_type="application/problem+json",
        headers=headers,
        content={
            "type": "about:blank",
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": str(request.url.path),
            "code": code,
            "correlationId": correlation_id,
            "recoverable": recoverable,
            **(extensions or {}),
        },
    )


async def api_error_exception_handler(request: Request, exc: ApiError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "")
    problem = exc.to_problem_details(
        correlation_id=correlation_id,
        instance=str(request.url.path),
    )

    headers = {"X-Correlation-ID": correlation_id} if correlation_id else None
    return JSONResponse(
        status_code=problem.status,
        media_type="application/problem+json",
        headers=headers,
        content=problem.to_dict(),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _problem_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        title="Validation Error",
        detail="Request validation failed.",
        recoverable=True,
        extensions={"errors": exc.errors()},
    )
