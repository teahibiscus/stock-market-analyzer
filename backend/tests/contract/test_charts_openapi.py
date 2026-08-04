from contextlib import nullcontext

from fastapi import FastAPI

from stock_market_analyzer.modules.market_data.api.router import create_market_data_router
from stock_market_analyzer.modules.market_data.infrastructure.provider.demo_provider import (
    DemoMarketDataProvider,
)


def test_chart_endpoint_is_canonical_and_legacy_history_is_deprecated() -> None:
    app = FastAPI()
    app.include_router(
        create_market_data_router(
            provider_factory=lambda: nullcontext(DemoMarketDataProvider()),
            data_source="demo",
            stream_interval_seconds=1,
        ),
        prefix="/api/v1",
    )

    paths = app.openapi()["paths"]
    assert paths["/api/v1/charts/{instrument_id}"]["get"]["operationId"] == "getInstrumentChart"
    assert paths["/api/v1/market-data/candles"]["get"]["deprecated"] is True
