from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class InstrumentNotFoundError(ValueError):
    """The canonical instrument identifier does not resolve to an active instrument."""


@dataclass(frozen=True, slots=True)
class ResolvedInstrument:
    instrument_id: str
    symbol: str


@runtime_checkable
class InstrumentResolver(Protocol):
    def resolve(self, instrument_id: str) -> ResolvedInstrument:
        """Resolve a canonical identifier without exposing catalog persistence."""
        ...
