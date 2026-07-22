from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel

HealthStatus = Literal["ok"]
ReadinessStatus = Literal["ready", "not_ready"]
DependencyStatus = Literal["up", "down"]


class HealthResponse(BaseModel):
    status: HealthStatus


class DependencyCheck(BaseModel):
    status: DependencyStatus


class ReadinessChecks(BaseModel):
    database: DependencyCheck
    redis: DependencyCheck


class ReadinessResponse(BaseModel):
    status: ReadinessStatus
    checks: ReadinessChecks


def create_health_router(
    *,
    database_health_checker: Callable[[], bool],
    cache_health_checker: Callable[[], bool],
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @router.get("/ready", response_model=ReadinessResponse)
    def ready(response: Response) -> ReadinessResponse:
        database_healthy = database_health_checker()
        cache_healthy = cache_health_checker()
        checks = ReadinessChecks(
            database=DependencyCheck(status="up" if database_healthy else "down"),
            redis=DependencyCheck(status="up" if cache_healthy else "down"),
        )
        payload = ReadinessResponse(
            status="ready" if database_healthy and cache_healthy else "not_ready",
            checks=checks,
        )

        if not (database_healthy and cache_healthy):
            response.status_code = 503

        return payload

    return router
