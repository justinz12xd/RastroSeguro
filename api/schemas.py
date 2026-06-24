"""Shared API schemas and response helpers."""

from __future__ import annotations

import math
from typing import Literal
from typing import Any

from pydantic import BaseModel, Field


def json_safe(value: Any) -> Any:
    """Recursively replace NaN/Infinity floats with None.

    Pandas marks missing numeric cells as float('nan'); Starlette's JSONResponse
    serializes with allow_nan=False, so any NaN/Inf reaching the wire raises
    'Out of range float values are not JSON compliant' and the request 500s.
    Applied at the envelope so every response (run_endpoint and direct
    success()/failure() callers like the agent) is covered. numpy float64 is a
    float subclass, so it is caught too.
    """
    if isinstance(value, float):
        return None if (math.isnan(value) or math.isinf(value)) else value
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


class ChatTurn(BaseModel):
    role: str
    content: str


class AgentAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    history: list[ChatTurn] | None = None
    selected_claim_id: str | None = None
    runtime: Literal["classic", "langgraph"] = "langgraph"
    user_role: Literal["analyst", "executive"] = "analyst"


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = "anonymous"
    thread_id: str | None = None
    selected_claim_id: str | None = None
    role: Literal["user"] = "user"
    runtime: Literal["classic", "langgraph"] = "langgraph"
    user_role: Literal["analyst", "executive"] = "analyst"
    persist: bool = True
    ui_context: dict[str, Any] | None = None


class ConfirmExtractedDocumentRequest(BaseModel):
    document_id: str | None = None
    filename: str | None = None
    claim: dict[str, Any] = Field(default_factory=dict)


def success(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": json_safe(data), "error": None}


def failure(message: str, hint: str | None = None, details: Any | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "data": None,
        "error": {
            "message": message,
            "hint": hint,
            "details": json_safe(details),
        },
    }
