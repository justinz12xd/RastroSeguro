"""SQLite-backed chat history and thread context for the antifraud assistant."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_HISTORY_DB = Path("db/chat_history.sqlite")
DEFAULT_USER_ID = "anonymous"
_UNSET = object()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dump(payload: dict[str, Any] | list[Any] | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=True)


def _json_load(payload: str | None, default: Any) -> Any:
    if not payload:
        return default
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return default


def _title_from_message(message: str, fallback: str = "Nueva sesion") -> str:
    words = " ".join(message.strip().split())
    if not words:
        return fallback
    return words[:56] + ("..." if len(words) > 56 else "")


class ChatHistoryStore:
    """Persist chat threads and messages without adding external DB dependencies."""

    def __init__(self, db_path: str | Path | None = None):
        configured = db_path or os.environ.get("RASTRO_AGENT_HISTORY_DB")
        self.db_path = Path(configured) if configured else DEFAULT_HISTORY_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_threads (
                    thread_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL DEFAULT 'anonymous',
                    title TEXT NOT NULL DEFAULT 'Nueva sesion',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    selected_claim_id TEXT,
                    last_claim_id TEXT,
                    last_intent TEXT,
                    current_section_id TEXT,
                    runtime TEXT NOT NULL DEFAULT 'langgraph',
                    state_json TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    section_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    intent TEXT,
                    source TEXT,
                    metadata_json TEXT,
                    data_json TEXT,
                    FOREIGN KEY(thread_id) REFERENCES agent_threads(thread_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_sections (
                    section_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT 'anonymous',
                    title TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'general',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT,
                    FOREIGN KEY(thread_id) REFERENCES agent_threads(thread_id)
                )
                """
            )
            self._ensure_column(connection, "agent_threads", "user_id", "TEXT NOT NULL DEFAULT 'anonymous'")
            self._ensure_column(connection, "agent_threads", "title", "TEXT NOT NULL DEFAULT 'Nueva sesion'")
            self._ensure_column(connection, "agent_threads", "current_section_id", "TEXT")
            self._ensure_column(connection, "agent_messages", "section_id", "TEXT")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_threads_user_updated ON agent_threads(user_id, updated_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_thread_section ON agent_messages(thread_id, section_id, id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_sections_thread ON agent_sections(thread_id, created_at)"
            )

    def _ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def prepare_thread(
        self,
        thread_id: str | None = None,
        *,
        user_id: str = DEFAULT_USER_ID,
        selected_claim_id: str | None | object = _UNSET,
        runtime: str = "langgraph",
        title: str | None = None,
        user_role: str = "analyst",
    ) -> dict[str, Any]:
        now = _utc_now()
        resolved_thread_id = thread_id or str(uuid4())
        resolved_user_id = user_id or DEFAULT_USER_ID
        with closing(self._connect()) as connection, connection:
            existing = connection.execute(
                "SELECT thread_id, user_id, state_json FROM agent_threads WHERE thread_id = ?",
                (resolved_thread_id,),
            ).fetchone()
            if existing is not None and existing["user_id"] != resolved_user_id:
                raise ValueError(f"No existe el thread {resolved_thread_id}.")
            row = existing
            if row is None:
                connection.execute(
                    """
                    INSERT INTO agent_threads (
                        thread_id, user_id, title, created_at, updated_at, selected_claim_id, runtime, state_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resolved_thread_id,
                        resolved_user_id,
                        title or "Nueva sesion",
                        now,
                        now,
                        selected_claim_id,
                        runtime,
                        _json_dump({"user_role": user_role}),
                    ),
                )
            else:
                next_state = _json_load(row["state_json"], {})
                next_state["user_role"] = user_role
                selected_claim_clause = (
                    "selected_claim_id = ?,"
                    if selected_claim_id is not _UNSET
                    else "selected_claim_id = selected_claim_id,"
                )
                params: list[Any] = [now]
                if selected_claim_id is not _UNSET:
                    params.append(selected_claim_id)
                params.extend([runtime, _json_dump(next_state), resolved_thread_id, resolved_user_id])
                connection.execute(
                    f"""
                    UPDATE agent_threads
                    SET updated_at = ?,
                        {selected_claim_clause}
                        runtime = ?,
                        state_json = ?
                    WHERE thread_id = ? AND user_id = ?
                    """,
                    params,
                )
        return self.get_thread(resolved_thread_id, user_id=resolved_user_id)

    def append_message(
        self,
        thread_id: str,
        *,
        user_id: str = DEFAULT_USER_ID,
        section_id: str | None = None,
        role: str,
        content: str,
        intent: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
        data: Any = None,
    ) -> dict[str, Any]:
        now = _utc_now()
        resolved_user_id = user_id or DEFAULT_USER_ID
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """
                INSERT INTO agent_messages (
                    thread_id, section_id, role, content, created_at, intent, source, metadata_json, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    section_id,
                    role,
                    content,
                    now,
                    intent,
                    source,
                    _json_dump(metadata),
                    _json_dump(data),
                ),
            )
            connection.execute(
                "UPDATE agent_threads SET updated_at = ? WHERE thread_id = ? AND user_id = ?",
                (now, thread_id, resolved_user_id),
            )
            if section_id:
                connection.execute(
                    """
                    UPDATE agent_sections
                    SET updated_at = ?, message_count = message_count + 1
                    WHERE section_id = ? AND thread_id = ? AND user_id = ?
                    """,
                    (now, section_id, thread_id, resolved_user_id),
                )
            message_id = cursor.lastrowid

        return {
            "id": str(message_id),
            "section_id": section_id,
            "role": role,
            "content": content,
            "timestamp": now,
            "intent": intent,
            "source": source,
            "metadata": metadata or {},
        }

    def assign_latest_user_message_to_section(self, thread_id: str, *, user_id: str, section_id: str) -> None:
        resolved_user_id = user_id or DEFAULT_USER_ID
        now = _utc_now()
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT id
                FROM agent_messages
                WHERE thread_id = ? AND role = 'user' AND section_id IS NULL
                ORDER BY id DESC
                LIMIT 1
                """,
                (thread_id,),
            ).fetchone()
            if row is None:
                return
            connection.execute(
                "UPDATE agent_messages SET section_id = ? WHERE id = ?",
                (section_id, row["id"]),
            )
            connection.execute(
                """
                UPDATE agent_sections
                SET updated_at = ?, message_count = message_count + 1
                WHERE section_id = ? AND thread_id = ? AND user_id = ?
                """,
                (now, section_id, thread_id, resolved_user_id),
            )

    def update_context(
        self,
        thread_id: str,
        *,
        user_id: str = DEFAULT_USER_ID,
        selected_claim_id: str | None | object = _UNSET,
        last_claim_id: str | None = None,
        last_intent: str | None = None,
        current_section_id: str | None = None,
        runtime: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_user_id = user_id or DEFAULT_USER_ID
        current = self.get_thread(thread_id, user_id=resolved_user_id)
        current_context = dict(current["context"])
        current_state = dict(current_context.get("state") or {})
        if state:
            current_state.update(state)

        next_selected_claim_id = current_context.get("selected_claim_id") if selected_claim_id is _UNSET else selected_claim_id
        next_last_claim_id = last_claim_id or current_context.get("last_claim_id")
        next_last_intent = last_intent or current_context.get("last_intent")
        next_section_id = current_section_id or current_context.get("current_section_id")
        next_runtime = runtime or current_context.get("runtime") or "langgraph"

        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                UPDATE agent_threads
                SET
                    updated_at = ?,
                    selected_claim_id = ?,
                    last_claim_id = ?,
                    last_intent = ?,
                    current_section_id = ?,
                    runtime = ?,
                    state_json = ?
                WHERE thread_id = ? AND user_id = ?
                """,
                (
                    _utc_now(),
                    next_selected_claim_id,
                    next_last_claim_id,
                    next_last_intent,
                    next_section_id,
                    next_runtime,
                    _json_dump(current_state),
                    thread_id,
                    resolved_user_id,
                ),
            )
        return self.get_thread(thread_id, user_id=resolved_user_id)

    def ensure_section(
        self,
        thread_id: str,
        *,
        user_id: str = DEFAULT_USER_ID,
        title: str,
        kind: str = "general",
        metadata: dict[str, Any] | None = None,
        reuse_section_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_user_id = user_id or DEFAULT_USER_ID
        now = _utc_now()
        with closing(self._connect()) as connection, connection:
            if reuse_section_id:
                row = connection.execute(
                    """
                    SELECT section_id, thread_id, user_id, title, kind, created_at, updated_at, message_count, metadata_json
                    FROM agent_sections
                    WHERE section_id = ? AND thread_id = ? AND user_id = ?
                    """,
                    (reuse_section_id, thread_id, resolved_user_id),
                ).fetchone()
                if row:
                    return self._section_from_row(row)

            section_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO agent_sections (
                    section_id, thread_id, user_id, title, kind, created_at, updated_at, message_count, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    section_id,
                    thread_id,
                    resolved_user_id,
                    title,
                    kind,
                    now,
                    now,
                    _json_dump(metadata or {}),
                ),
            )
        return self.get_section(section_id, user_id=resolved_user_id)

    def choose_section(
        self,
        thread: dict[str, Any],
        *,
        user_id: str,
        intent: str | None,
        claim_id: str | None,
        message: str,
    ) -> dict[str, Any]:
        context = thread.get("context") or {}
        state = context.get("state") or {}
        current_section_id = context.get("current_section_id")
        previous_intent = state.get("section_intent")
        previous_claim_id = state.get("section_claim_id")
        next_intent = intent or "general"
        next_claim_id = claim_id

        if current_section_id and previous_intent == next_intent and previous_claim_id == next_claim_id:
            return self.ensure_section(
                thread["thread_id"],
                user_id=user_id,
                title="Conversacion",
                reuse_section_id=current_section_id,
            )

        if next_claim_id:
            title = f"Caso {next_claim_id}"
            kind = "claim"
        elif next_intent and next_intent != "general":
            title = next_intent.replace("_", " ").title()
            kind = "intent"
        else:
            title = _title_from_message(message, fallback="Conversacion")
            kind = "general"

        return self.ensure_section(
            thread["thread_id"],
            user_id=user_id,
            title=title,
            kind=kind,
            metadata={"intent": next_intent, "claim_id": next_claim_id},
        )

    def get_section(self, section_id: str, *, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        resolved_user_id = user_id or DEFAULT_USER_ID
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT section_id, thread_id, user_id, title, kind, created_at, updated_at, message_count, metadata_json
                FROM agent_sections
                WHERE section_id = ? AND user_id = ?
                """,
                (section_id, resolved_user_id),
            ).fetchone()
            if row is None:
                raise ValueError(f"No existe la seccion {section_id}.")
        return self._section_from_row(row)

    def list_threads(self, *, user_id: str = DEFAULT_USER_ID, limit: int = 25) -> list[dict[str, Any]]:
        resolved_user_id = user_id or DEFAULT_USER_ID
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT
                    t.thread_id,
                    t.user_id,
                    t.title,
                    t.created_at,
                    t.updated_at,
                    t.selected_claim_id,
                    t.last_claim_id,
                    t.last_intent,
                    t.runtime,
                    COUNT(m.id) AS message_count
                FROM agent_threads t
                LEFT JOIN agent_messages m ON m.thread_id = t.thread_id
                WHERE t.user_id = ?
                GROUP BY t.thread_id
                ORDER BY t.updated_at DESC
                LIMIT ?
                """,
                (resolved_user_id, limit),
            ).fetchall()
        return [
            {
                "thread_id": row["thread_id"],
                "user_id": row["user_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "selected_claim_id": row["selected_claim_id"],
                "last_claim_id": row["last_claim_id"],
                "last_intent": row["last_intent"],
                "runtime": row["runtime"],
                "message_count": int(row["message_count"] or 0),
            }
            for row in rows
        ]

    def get_thread(self, thread_id: str, *, user_id: str = DEFAULT_USER_ID, limit: int = 100) -> dict[str, Any]:
        resolved_user_id = user_id or DEFAULT_USER_ID
        with closing(self._connect()) as connection, connection:
            thread = connection.execute(
                """
                SELECT thread_id, user_id, title, created_at, updated_at, selected_claim_id, last_claim_id, last_intent, current_section_id, runtime, state_json
                FROM agent_threads
                WHERE thread_id = ? AND user_id = ?
                """,
                (thread_id, resolved_user_id),
            ).fetchone()
            if thread is None:
                raise ValueError(f"No existe el thread {thread_id}.")

            rows = connection.execute(
                """
                SELECT id, section_id, role, content, created_at, intent, source, metadata_json, data_json
                FROM (
                    SELECT id, section_id, role, content, created_at, intent, source, metadata_json, data_json
                    FROM agent_messages
                    WHERE thread_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                ) recent_messages
                ORDER BY id ASC
                """,
                (thread_id, limit),
            ).fetchall()
            sections = connection.execute(
                """
                SELECT section_id, thread_id, user_id, title, kind, created_at, updated_at, message_count, metadata_json
                FROM agent_sections
                WHERE thread_id = ? AND user_id = ?
                ORDER BY created_at ASC
                """,
                (thread_id, resolved_user_id),
            ).fetchall()

        history = [
            {
                "id": str(row["id"]),
                "section_id": row["section_id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["created_at"],
                "intent": row["intent"],
                "source": row["source"],
                "metadata": _json_load(row["metadata_json"], {}),
                "data": _json_load(row["data_json"], None),
            }
            for row in rows
        ]

        return {
            "thread_id": thread["thread_id"],
            "user_id": thread["user_id"],
            "title": thread["title"],
            "history": history,
            "sections": [self._section_from_row(row) for row in sections],
            "context": {
                "selected_claim_id": thread["selected_claim_id"],
                "last_claim_id": thread["last_claim_id"],
                "last_intent": thread["last_intent"],
                "current_section_id": thread["current_section_id"],
                "runtime": thread["runtime"],
                "state": _json_load(thread["state_json"], {}),
            },
            "created_at": thread["created_at"],
            "updated_at": thread["updated_at"],
        }

    def rename_thread_from_first_message(self, thread_id: str, *, user_id: str, message: str) -> None:
        resolved_user_id = user_id or DEFAULT_USER_ID
        title = _title_from_message(message)
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT title FROM agent_threads WHERE thread_id = ? AND user_id = ?",
                (thread_id, resolved_user_id),
            ).fetchone()
            if row and row["title"] == "Nueva sesion":
                connection.execute(
                    "UPDATE agent_threads SET title = ? WHERE thread_id = ? AND user_id = ?",
                    (title, thread_id, resolved_user_id),
                )

    def _section_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "section_id": row["section_id"],
            "thread_id": row["thread_id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "kind": row["kind"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": int(row["message_count"] or 0),
            "metadata": _json_load(row["metadata_json"], {}),
        }
