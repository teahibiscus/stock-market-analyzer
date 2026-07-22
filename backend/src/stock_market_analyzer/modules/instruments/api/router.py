from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Query, Request

from stock_market_analyzer.modules.instruments.api.schemas import InstrumentSearchResponse
from stock_market_analyzer.modules.instruments.application.search_instruments import (
    InvalidInstrumentSearchQuery,
    SearchInstruments,
)
from stock_market_analyzer.modules.instruments.ports.instrument_reference_provider import (
    InstrumentReferenceDependencyError,
    InstrumentReferencePersistenceError,
    InstrumentReferenceProvider,
)
from stock_market_analyzer.shared.kernel.errors.api_error import ApiError

InstrumentProviderFactory = Callable[[], AbstractContextManager[InstrumentReferenceProvider]]
logger = logging.getLogger("stock_market_analyzer.instruments.search")


def create_instrument_router(
    *,
    provider_factory: InstrumentProviderFactory,
    result_limit: int,
) -> APIRouter:
    router = APIRouter(prefix="/instruments", tags=["instruments"])

    @router.get(
        "/search",
        operation_id="searchInstruments",
        summary="Search instruments",
        description="Return supported instruments matching a symbol or company name.",
        response_model=InstrumentSearchResponse,
        responses={
            422: {"description": "The search query is missing or invalid."},
            503: {"description": "Instrument reference data is temporarily unavailable."},
        },
    )
    def search_instruments(
        request: Request,
        q: Annotated[
            str,
            Query(
                max_length=100,
                description="Non-empty symbol or company name to search for.",
            ),
        ],
    ) -> InstrumentSearchResponse:
        started_at = perf_counter()
        correlation_id = getattr(request.state, "correlation_id", "")

        try:
            with provider_factory() as provider:
                results = SearchInstruments(
                    provider=provider,
                    result_limit=result_limit,
                ).execute(q)
        except InvalidInstrumentSearchQuery as exc:
            raise ApiError(
                code="VALIDATION_ERROR",
                message=str(exc),
                status_code=422,
                recoverable=True,
                extensions={
                    "errors": [
                        {
                            "type": "value_error",
                            "loc": ["query", "q"],
                            "msg": str(exc),
                            "input": q,
                        }
                    ]
                },
            ) from exc
        except InstrumentReferencePersistenceError as exc:
            _log_failure(
                correlation_id=correlation_id,
                started_at=started_at,
                error_code="PERSISTENCE_ERROR",
            )
            raise ApiError(
                code="PERSISTENCE_ERROR",
                message="Instrument search is temporarily unavailable.",
                status_code=503,
                recoverable=True,
            ) from exc
        except InstrumentReferenceDependencyError as exc:
            _log_failure(
                correlation_id=correlation_id,
                started_at=started_at,
                error_code="DEPENDENCY_ERROR",
            )
            raise ApiError(
                code="DEPENDENCY_ERROR",
                message="Instrument reference data is temporarily unavailable.",
                status_code=503,
                recoverable=True,
            ) from exc

        response = InstrumentSearchResponse.from_results(results)
        logger.info(
            "instrument_search_completed",
            extra={
                "application_state": response.metadata.state.value,
                "correlation_id": correlation_id,
                "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                "result_count": len(results),
            },
        )
        return response

    return router


def _log_failure(*, correlation_id: str, started_at: float, error_code: str) -> None:
    logger.warning(
        "instrument_search_failed",
        extra={
            "correlation_id": correlation_id,
            "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            "error_code": error_code,
        },
    )
