from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProblemDetails:
    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    correlation_id: str
    recoverable: bool
    extensions: dict[str, Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
            "code": self.code,
            "correlationId": self.correlation_id,
            "recoverable": self.recoverable,
        }

        if self.extensions:
            payload.update(self.extensions)

        return payload
