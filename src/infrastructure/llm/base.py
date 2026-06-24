"""Small provider contract for optional conversational synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMRequest:
    """Structured context passed from deterministic tools to an LLM provider."""

    intent: str
    data: Any
    question: str
    history: Any = None
    user_role: str = "analyst"


@dataclass(frozen=True)
class LLMResult:
    """Provider result that never raises into the antifraud agent facade."""

    message: str | None
    provider: str
    model: str | None = None
    status: str = "disabled"
    enabled: bool = False
    error: str | None = None

    @property
    def has_message(self) -> bool:
        return bool(self.message and self.message.strip())

    def metadata(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
        }
        if self.error:
            meta["error"] = self.error
        return meta


class LLMProvider(Protocol):
    """Minimal interface for optional LLM-backed response synthesis."""

    def generate(self, request: LLMRequest) -> LLMResult:
        """Generate a natural-language response from verified tool output."""
