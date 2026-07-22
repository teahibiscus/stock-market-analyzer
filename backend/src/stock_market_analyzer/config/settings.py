from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Stock Market Analyzer API"
    environment: str = "development"
    log_level: str = "INFO"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_origin: str = "http://127.0.0.1:3000"
    database_url: str = (
        "postgresql+psycopg://stock_market_analyzer:replace-with-local-only-password"
        "@localhost:5432/stock_market_analyzer"
    )
    redis_url: str = "redis://localhost:6379/0"
    instrument_search_limit: int = Field(default=20, ge=1, le=100)


def get_settings() -> Settings:
    return Settings()
