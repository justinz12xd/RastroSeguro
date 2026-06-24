"""Antifraud agent routes."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.routes._errors import run_endpoint
from api.schemas import AgentAskRequest, AgentChatRequest, failure, success
from src.agent.antifraud_agent import answer_question, get_quick_questions
from src.infrastructure.chat.chat_history import ChatHistoryStore
from src.agent.entities import extract_claim_id
from src.application.agent.chat_service import run_chat

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _chat_store() -> ChatHistoryStore:
    return ChatHistoryStore()


@router.get("/quick-questions")
def quick_questions(user_role: str = Query(default="analyst")) -> dict:
    return success(get_quick_questions(user_role=user_role))


@router.post("/ask")
def ask_agent(payload: AgentAskRequest):
    history = [turn.model_dump() for turn in payload.history] if payload.history else None
    response = answer_question(
        payload.question,
        history=history,
        selected_claim_id=payload.selected_claim_id,
        runtime=payload.runtime,
        user_role=payload.user_role,
    )
    if response.get("ok") is False:
        return JSONResponse(
            status_code=400,
            content=failure(
                str(response.get("message", "El agente no pudo responder.")),
                hint=response.get("hint"),
                details=response,
            ),
        )
    return success(response)


@router.get("/threads/{thread_id}")
def get_agent_thread(thread_id: str, user_id: str = Query(default="anonymous")):
    return run_endpoint(lambda: _chat_store().get_thread(thread_id, user_id=user_id))


@router.get("/sessions")
def list_agent_sessions(user_id: str = Query(default="anonymous"), limit: int = Query(default=25, ge=1, le=100)):
    return run_endpoint(lambda: _chat_store().list_threads(user_id=user_id, limit=limit))


@router.post("/chat")
def chat_agent(payload: AgentChatRequest):
    return run_endpoint(
        lambda: run_chat(
            payload,
            store=_chat_store(),
            answer_fn=answer_question,
            extract_claim_id=extract_claim_id,
        )
    )
