"""Use case: drive a persisted antifraud-agent chat turn.

Orchestrates the chat store (thread prep, message persistence, sectioning) and
the agent's ``answer_question`` into a single response payload. Extracted from
the FastAPI handler so the orchestration is testable without HTTP and the route
stays a thin adapter.

Collaborators are injected (``store``, ``answer_fn``, ``extract_claim_id``)
rather than imported here: this keeps the application layer free of a hard
dependency on a concrete store/agent and preserves the route-level patch points
used by the existing API tests.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol


class _ChatStore(Protocol):
    def prepare_thread(self, thread_id, *, user_id, selected_claim_id, runtime, user_role): ...
    def append_message(self, thread_id, *, user_id, role, content, **kwargs): ...
    def rename_thread_from_first_message(self, thread_id, *, user_id, message): ...
    def choose_section(self, thread, *, user_id, intent, claim_id, message): ...
    def assign_latest_user_message_to_section(self, thread_id, *, user_id, section_id): ...
    def update_context(self, thread_id, *, user_id, **kwargs): ...


def run_chat(
    payload: Any,
    *,
    store: _ChatStore,
    answer_fn: Callable[..., dict],
    extract_claim_id: Callable[[str], str | None],
) -> dict[str, Any]:
    """Run one chat turn and return the serialized thread state + agent reply."""
    user_id = payload.user_id or "anonymous"
    thread = store.prepare_thread(
        payload.thread_id,
        user_id=user_id,
        selected_claim_id=payload.selected_claim_id,
        runtime=payload.runtime,
        user_role=payload.user_role,
    )
    thread_id = thread["thread_id"]
    history = thread["history"]

    if payload.persist:
        store.append_message(
            thread_id,
            user_id=user_id,
            role=payload.role,
            content=payload.message,
        )
        store.rename_thread_from_first_message(thread_id, user_id=user_id, message=payload.message)

    updated_history = [*history, {"role": payload.role, "content": payload.message}]
    reply = answer_fn(
        payload.message,
        history=updated_history,
        selected_claim_id=payload.selected_claim_id or thread["context"].get("last_claim_id"),
        thread_id=thread_id,
        runtime=payload.runtime,
        user_role=payload.user_role,
    )

    assistant_source = reply.get("source", "agent")
    context = reply.get("context") or {}
    resolved_claim_id = context.get("resolved_claim_id") or extract_claim_id(payload.message)
    section = None
    if payload.persist:
        section = store.choose_section(
            thread,
            user_id=user_id,
            intent=reply.get("intent"),
            claim_id=resolved_claim_id,
            message=payload.message,
        )
        store.assign_latest_user_message_to_section(
            thread_id,
            user_id=user_id,
            section_id=section["section_id"],
        )
        store.append_message(
            thread_id,
            user_id=user_id,
            section_id=section["section_id"],
            role="assistant",
            content=str(reply.get("message", "")),
            intent=reply.get("intent"),
            source=assistant_source,
            metadata={
                "ok": reply.get("ok", False),
                "runtime": reply.get("runtime"),
                "llm": reply.get("llm"),
            },
            data=reply.get("data"),
        )

    selected_claim_id = payload.selected_claim_id or thread["context"].get("selected_claim_id")
    thread_state: dict = {
        "last_ok": bool(reply.get("ok")),
        "last_source": assistant_source,
        "user_role": payload.user_role,
        "section_intent": reply.get("intent"),
        "section_claim_id": resolved_claim_id,
    }
    if payload.ui_context:
        thread_state["ui_context"] = payload.ui_context
    if payload.persist:
        updated_thread = store.update_context(
            thread_id,
            user_id=user_id,
            selected_claim_id=selected_claim_id,
            last_claim_id=resolved_claim_id,
            last_intent=reply.get("intent"),
            current_section_id=section["section_id"] if section else None,
            runtime=(reply.get("runtime") or {}).get("active"),
            state=thread_state,
        )
    else:
        updated_thread = thread

    return {
        "thread_id": thread_id,
        "user_id": updated_thread["user_id"],
        "title": updated_thread["title"],
        "reply": reply,
        "history": updated_thread["history"],
        "sections": updated_thread["sections"],
        "context": updated_thread["context"],
        "created_at": updated_thread["created_at"],
        "updated_at": updated_thread["updated_at"],
    }
