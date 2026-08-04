"""Background worker commands for controlled market-data jobs."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from stock_market_analyzer.config.settings import get_settings
from stock_market_analyzer.modules.instruments.infrastructure.persistence.models import (
    InstrumentModel,
    InstrumentSymbolModel,
)
from stock_market_analyzer.modules.market_data.application.backfill_candles import BackfillCandles
from stock_market_analyzer.modules.market_data.domain.timeframe import Interval, Period
from stock_market_analyzer.modules.market_data.infrastructure.persistence.repository import (
    SqlAlchemyCandleRepository,
)
from stock_market_analyzer.modules.market_data.infrastructure.provider.demo_provider import (
    DemoMarketDataProvider,
)
from stock_market_analyzer.shared.infrastructure.database.health import create_database_engine


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="stock-market-analyzer-worker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    backfill = subparsers.add_parser("backfill", help="Backfill canonical OHLCV bars.")
    backfill.add_argument("--interval", choices=[item.value for item in Interval], default="1d")
    backfill.add_argument("--period", choices=[item.value for item in Period], default="1y")
    backfill.add_argument("--instrument-id")
    args = parser.parse_args(argv)

    if args.command == "backfill":
        count = _run_backfill(
            interval=Interval(args.interval),
            period=Period(args.period),
            instrument_id=args.instrument_id,
        )
        print(f"Backfilled {count} candles.")


def _run_backfill(*, interval: Interval, period: Period, instrument_id: str | None) -> int:
    settings = get_settings()
    engine = create_database_engine(settings)
    provider = DemoMarketDataProvider()
    with Session(engine) as session:
        statement = (
            select(InstrumentModel.id, InstrumentSymbolModel.symbol)
            .join(
                InstrumentSymbolModel,
                InstrumentSymbolModel.instrument_id == InstrumentModel.id,
            )
            .where(
                InstrumentModel.status == "ACTIVE",
                InstrumentSymbolModel.is_primary.is_(True),
            )
            .order_by(InstrumentModel.id)
        )
        if instrument_id:
            statement = statement.where(InstrumentModel.id == instrument_id)
        rows = session.execute(statement).all()
        repository = SqlAlchemyCandleRepository(session)
        use_case = BackfillCandles(
            provider=provider,
            repository=repository,
            data_source=settings.market_data_source,
        )
        return sum(
            use_case.execute(
                instrument_id=row.id,
                symbol=row.symbol,
                interval=interval,
                period=period,
            )
            for row in rows
        )


if __name__ == "__main__":
    main()
