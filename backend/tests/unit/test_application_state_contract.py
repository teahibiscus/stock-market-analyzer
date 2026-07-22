from __future__ import annotations

from datetime import UTC, datetime

from stock_market_analyzer.modules.application_state.domain.enums import (
    APPLICATION_STATE_VALUES,
    FRESHNESS_STATE_VALUES,
    ApplicationState,
    FreshnessState,
)
from stock_market_analyzer.modules.application_state.domain.metadata import (
    ApplicationStateMetadata,
    FreshnessMetadata,
)


def test_application_state_enum_contains_required_mvp_values() -> None:
    assert set(APPLICATION_STATE_VALUES) == {
        "LOADING",
        "SUCCESS",
        "EMPTY",
        "UNAVAILABLE",
        "DELAYED",
        "VALIDATION_ERROR",
        "PERMISSION_DENIED",
        "TIMEOUT",
        "DEPENDENCY_ERROR",
        "PERSISTENCE_ERROR",
        "PARTIAL_SUCCESS",
    }


def test_freshness_state_enum_contains_required_mvp_values() -> None:
    assert set(FRESHNESS_STATE_VALUES) == {
        "FRESH",
        "DELAYED",
        "STALE",
        "UNAVAILABLE",
        "UNKNOWN",
    }


def test_application_state_metadata_serializes_to_contract_shape() -> None:
    metadata = ApplicationStateMetadata(
        state=ApplicationState.DELAYED,
        code="MARKET_DATA_DELAYED",
        recoverable=True,
        retry_after_seconds=30,
        freshness=FreshnessMetadata(
            provider_timestamp=datetime(2026, 7, 10, 17, 30, tzinfo=UTC),
            ingested_at=datetime(2026, 7, 10, 17, 30, 4, tzinfo=UTC),
            delay_seconds=900,
            state=FreshnessState.DELAYED,
        ),
        warnings=[],
    )

    payload = metadata.model_dump(mode="json", by_alias=True)

    assert payload == {
        "state": "DELAYED",
        "code": "MARKET_DATA_DELAYED",
        "recoverable": True,
        "retryAfterSeconds": 30,
        "freshness": {
            "providerTimestamp": "2026-07-10T17:30:00Z",
            "ingestedAt": "2026-07-10T17:30:04Z",
            "delaySeconds": 900,
            "state": "DELAYED",
        },
        "warnings": [],
    }
