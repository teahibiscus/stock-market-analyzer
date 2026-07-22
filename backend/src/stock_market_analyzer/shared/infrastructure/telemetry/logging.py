import logging

from stock_market_analyzer.config.settings import Settings


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level,
        format=(
            "%(asctime)s %(levelname)s "
            "[service=stock-market-analyzer-api correlation_id=%(correlation_id)s] "
            "%(message)s"
        ),
        force=True,
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(CorrelationIdFilter())

    logging.getLogger().setLevel(settings.log_level)
