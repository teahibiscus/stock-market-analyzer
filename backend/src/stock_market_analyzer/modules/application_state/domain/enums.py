from __future__ import annotations

from enum import StrEnum


class ApplicationState(StrEnum):
    LOADING = "LOADING"
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    UNAVAILABLE = "UNAVAILABLE"
    DELAYED = "DELAYED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


class FreshnessState(StrEnum):
    FRESH = "FRESH"
    DELAYED = "DELAYED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


APPLICATION_STATE_VALUES = tuple(state.value for state in ApplicationState)
FRESHNESS_STATE_VALUES = tuple(state.value for state in FreshnessState)
