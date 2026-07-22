import uvicorn

from stock_market_analyzer.app.composition_root.factory import create_app
from stock_market_analyzer.config.settings import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(settings=settings),
        host=settings.backend_host,
        port=settings.backend_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
