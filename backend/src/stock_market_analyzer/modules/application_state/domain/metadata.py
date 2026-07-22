from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from stock_market_analyzer.modules.application_state.domain.enums import (
    ApplicationState,
    FreshnessState,
)


class FreshnessMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    provider_timestamp: datetime | None = Field(
        default=None, serialization_alias="providerTimestamp"
    )
    ingested_at: datetime | None = Field(default=None, serialization_alias="ingestedAt")
    delay_seconds: int | None = Field(default=None, serialization_alias="delaySeconds")
    state: FreshnessState | None = None


class ApplicationStateMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    state: ApplicationState
    code: str
    recoverable: bool
    retry_after_seconds: int | None = Field(default=None, serialization_alias="retryAfterSeconds")
    freshness: FreshnessMetadata | None = None
    warnings: list[str] = Field(default_factory=list)
