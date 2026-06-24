# Agent Chat And LangGraph Runtime Design

## Goal

Introduce a persistent chat contract for the antifraud assistant without replacing the deterministic scoring core. The new flow should keep thread history on the backend, expose a stable `thread_id`, and allow an optional LangGraph-style runtime to orchestrate routing later.

## Scope

- Add `POST /api/agent/chat` with `thread_id`, `message`, `selected_claim_id`, and `runtime`.
- Persist threads and messages in SQLite using the Python standard library.
- Expose `GET /api/agent/threads/{thread_id}` for reload and resume.
- Preserve `/api/agent/ask` for current compatibility.
- Add an optional LangGraph runtime path with fallback to the current classic dispatcher when LangGraph is not installed.

## Architecture

### Backend

- `src/agent/chat_history.py` stores thread context and messages in `db/chat_history.sqlite`.
- `api/routes/agent.py` becomes the bridge between HTTP chat requests and the antifraud agent.
- `src/agent/antifraud_agent.py` remains the single facade for deterministic tools, RAG, and optional LLM synthesis.
- `src/agent/langgraph_runtime.py` encapsulates the optional graph runtime and does not become mandatory for the rest of the system.

### Frontend

- The assistant widget keeps a `thread_id` in local storage.
- On reopen, the widget loads backend history instead of relying only on in-memory React state.
- Message rendering still uses the existing UI; only the data source changes.

## Data Flow

1. The frontend sends `message`, optional `thread_id`, and optional `selected_claim_id`.
2. The backend creates or loads the thread.
3. The user message is persisted.
4. The agent resolves the intent and executes either the classic runtime or the LangGraph runtime.
5. The assistant reply is persisted.
6. The API returns the full history plus updated thread context.

## Error Handling

- Validation errors remain standard FastAPI envelope errors.
- Domain errors inside the chat become assistant replies stored in thread history.
- If LangGraph is requested but not installed, the system falls back to the classic runtime and marks that in runtime metadata.

## Testing

- Cover thread creation and history retrieval in API tests.
- Cover selected-claim fallback and runtime metadata in agent tests.
- Keep legacy `/api/agent/ask` behavior intact to avoid regressions in older UI code.
