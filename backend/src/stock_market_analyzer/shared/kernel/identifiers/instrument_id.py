from __future__ import annotations

from typing import NewType

InstrumentId = NewType("InstrumentId", str)


def parse_instrument_id(value: str) -> InstrumentId:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Instrument ID must not be empty.")
    return InstrumentId(normalized)
