"""No-op LLM provider used when conversational synthesis is disabled."""

from __future__ import annotations

from src.infrastructure.llm.base import LLMRequest, LLMResult


class DisabledProvider:
    """Preserves deterministic behavior when no LLM is configured."""

    def __init__(
        self,
        reason: str = "disabled",
        provider: str = "disabled",
        model: str | None = None,
        enabled: bool = False,
    ) -> None:
        self.reason = reason
        self.provider = provider
        self.model = model
        self.enabled = enabled

    def generate(self, request: LLMRequest) -> LLMResult:
        return LLMResult(
            message=None,
            provider=self.provider,
            model=self.model,
            status=self.reason,
            enabled=self.enabled,
        )
