from __future__ import annotations

from typing import Protocol, runtime_checkable

from stock_market_analyzer.modules.instruments.domain.instrument import Instrument


class InstrumentReferenceError(Exception):
    """Base failure exposed by instrument-reference adapters."""


class InstrumentReferencePersistenceError(InstrumentReferenceError):
    """Instrument reference persistence could not complete the request."""


class InstrumentReferenceDependencyError(InstrumentReferenceError):
    """An external instrument-reference dependency is unavailable."""


@runtime_checkable
class InstrumentReferenceProvider(Protocol):
    def search(self, query: str, *, limit: int) -> list[Instrument]:
        """Return canonical instruments matching a symbol or company name."""
        ...
