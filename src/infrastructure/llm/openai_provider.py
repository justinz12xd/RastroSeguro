"""OpenAI Responses API provider for optional RastroSeguro synthesis."""

from __future__ import annotations

from typing import Any

from src.infrastructure.llm.base import LLMRequest, LLMResult
from src.infrastructure.llm.prompts import SYSTEM_INSTRUCTIONS, build_user_input
from src.infrastructure.llm.settings import LLMSettings

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class OpenAIProvider:
    """Calls OpenAI only after deterministic RastroSeguro tools have run."""

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def generate(self, request: LLMRequest) -> LLMResult:
        if not self.settings.api_key:
            return LLMResult(None, provider="openai", model=self.settings.model, status="missing_api_key", enabled=True)

        payload = {
            "model": self.settings.model,
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": build_user_input(request.intent, request.data, request.question, request.history, request.user_role),
            "max_output_tokens": self.settings.max_output_tokens,
            "store": False,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = _post_json(
                OPENAI_RESPONSES_URL,
                payload=payload,
                headers=headers,
                timeout=self.settings.timeout_seconds,
            )
        except ModuleNotFoundError as exc:
            return LLMResult(
                None,
                provider="openai",
                model=self.settings.model,
                status="missing_dependency",
                enabled=True,
                error=str(exc),
            )
        except Exception as exc:
            return LLMResult(None, provider="openai", model=self.settings.model, status="request_error", enabled=True, error=str(exc))

        if response.status_code != 200:
            return LLMResult(
                None,
                provider="openai",
                model=self.settings.model,
                status=f"http_{response.status_code}",
                enabled=True,
                error=_response_error(response),
            )

        try:
            data = response.json()
        except ValueError as exc:
            return LLMResult(None, provider="openai", model=self.settings.model, status="invalid_json", enabled=True, error=str(exc))

        text = _extract_text(data)
        if not text:
            return LLMResult(None, provider="openai", model=self.settings.model, status="empty_response", enabled=True)

        return LLMResult(text, provider="openai", model=self.settings.model, status="ok", enabled=True)


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> Any:
    """Import requests lazily so the deterministic agent works without optional deps installed."""
    import requests

    return requests.post(url, json=payload, headers=headers, timeout=timeout)


def _extract_text(data: dict[str, Any]) -> str | None:
    """Support both output_text convenience field and raw Responses output blocks."""
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in data.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())

    if chunks:
        return "\n".join(chunks).strip()
    return None


def _response_error(response: Any) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:500]
    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict):
        return str(error.get("message") or error)
    return str(data)[:500]
