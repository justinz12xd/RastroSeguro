"""Shared models for auditable fraud rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["baja", "media", "alta", "critica"]


@dataclass(frozen=True)
class RuleResult:
    """Result emitted by a rule when a signal is detected."""

    code: str
    name: str
    points: float
    severity: Severity
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    pdf_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "code": self.code,
            "name": self.name,
            "points": round(float(self.points), 2),
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
            "category": self.category,
        }
        if self.pdf_ref:
            payload["pdf_ref"] = self.pdf_ref
        return payload
