from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from stock_market_analyzer.app.composition_root.factory import create_app


@pytest.fixture
def client_factory() -> Callable[..., TestClient]:
    def _create_client(
        *,
        database_healthy: bool = True,
        cache_healthy: bool = True,
    ) -> TestClient:
        return TestClient(
            create_app(
                database_health_checker=lambda: database_healthy,
                cache_health_checker=lambda: cache_healthy,
            )
        )

    return _create_client


def test_health_returns_ok_without_dependency_checks(
    client_factory: Callable[..., TestClient],
) -> None:
    client = client_factory()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_ready_when_dependencies_are_healthy(
    client_factory: Callable[..., TestClient],
) -> None:
    client = client_factory(database_healthy=True, cache_healthy=True)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": {"status": "up"},
            "redis": {"status": "up"},
        },
    }


def test_readiness_returns_service_unavailable_when_database_is_down(
    client_factory: Callable[..., TestClient],
) -> None:
    client = client_factory(database_healthy=False, cache_healthy=True)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": {"status": "down"},
            "redis": {"status": "up"},
        },
    }


def test_readiness_returns_service_unavailable_when_redis_is_down(
    client_factory: Callable[..., TestClient],
) -> None:
    client = client_factory(database_healthy=True, cache_healthy=False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": {"status": "up"},
            "redis": {"status": "down"},
        },
    }


def test_api_v1_router_is_mounted(client_factory: Callable[..., TestClient]) -> None:
    client = client_factory()

    response = client.get("/api/v1")

    assert response.status_code == 200
    assert response.json() == {"version": "v1"}
