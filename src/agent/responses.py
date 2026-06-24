"""Consistent response envelopes for the antifraud agent."""

from __future__ import annotations

from typing import Any


def success(
    intent: str,
    message: str,
    data: Any,
    source: str = "tools",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = {
        "ok": True,
        "intent": intent,
        "message": message,
        "data": data,
        "source": source,
    }
    if metadata:
        response.update(metadata)
    return response


def error(intent: str, message: str, hint: str | None = None) -> dict[str, Any]:
    response = {
        "ok": False,
        "intent": intent,
        "message": message,
        "data": None,
        "source": "agent",
    }
    if hint:
        response["hint"] = hint
    return response
