from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Stock Market Analyzer API"
    environment: str = "development"
    log_level: str = "INFO"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_origin: str = "http://127.0.0.1:3000"
    frontend_additional_origin: str | None = "http://localhost:3000"
    database_url: str = (
        "postgresql+psycopg://stock_market_analyzer:replace-with-local-only-password"
        "@localhost:5432/stock_market_analyzer"
    )
    redis_url: str = "redis://localhost:6379/0"
    instrument_search_limit: int = Field(default=20, ge=1, le=100)
    market_data_source: str = "demo"
    market_data_stream_interval_seconds: float = Field(default=1.0, gt=0)

    @field_validator("frontend_origin", "frontend_additional_origin")
    @classmethod
    def validate_frontend_origin(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().rstrip("/")
        if not normalized or normalized == "*":
            raise ValueError("Frontend origins must be explicit URLs.")
        return normalized


def get_settings() -> Settings:
    return Settings()
