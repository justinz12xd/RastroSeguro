"""Environment-backed settings for the optional LLM layer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL = "gpt-4o"


@dataclass(frozen=True)
class LLMSettings:
    enabled: bool
    provider: str
    model: str
    api_key: str | None
    timeout_seconds: float
    max_output_tokens: int


def load_dotenv(path: str | Path = ".env") -> None:
    """Load local .env values without overriding the real environment."""
    env_path = Path(path)
    if not env_path.exists():
        return

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except OSError:
        return


def load_settings() -> LLMSettings:
    load_dotenv()
    return LLMSettings(
        enabled=_as_bool(os.environ.get("RASTRO_LLM_ENABLED"), default=False),
        provider=os.environ.get("RASTRO_LLM_PROVIDER", "openai").strip().lower(),
        model=os.environ.get("RASTRO_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        api_key=os.environ.get("OPENAI_API_KEY"),
        timeout_seconds=_as_float(os.environ.get("RASTRO_LLM_TIMEOUT_SECONDS"), default=10.0),
        max_output_tokens=_as_int(os.environ.get("RASTRO_LLM_MAX_OUTPUT_TOKENS"), default=360),
    )


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
