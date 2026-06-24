"""Multi-agent runtime for the antifraud agent, built on LangGraph.

A **supervisor** agent classifies the question and delegates to one of several
**specialist worker agents**, each owning a domain and its toolset:

- ``portfolio_analyst`` — portfolio-wide analytics (top risk, rankings, cities,
  branches, frequency, atypical amounts, savings, executive summary…).
- ``case_investigator`` — single-claim investigation (explanation, dossier,
  similar narratives, graph connections).
- ``network_analyst`` — organised fraud rings / shared-entity networks.
- ``docs_specialist`` — methodology/rules/ethics answered from documentation (RAG).
- ``general_assistant`` — short utility turns such as date, greeting or help.

A final ``synthesizer`` consolidates the result. Every specialist is backed by
the same deterministic tools as the classic runtime, so the response **data
contract is identical**; the multi-agent layer adds explicit orchestration and a
trace of which agents participated (``runtime.agents``).

LangGraph is optional: if it is not installed, ``run_langgraph_turn`` raises
``LangGraphUnavailableError`` and the caller falls back to the classic runtime.
"""

from __future__ import annotations

import operator
from functools import lru_cache
from typing import Annotated, Any, Callable, TypedDict

from src.agent.intents import CLAIM_REQUIRED_INTENTS, GENERAL_INTENTS
from src.agent.router import route

# Intents that the single-claim investigator owns (claim-scoped analysis).
_CASE_INTENTS = set(CLAIM_REQUIRED_INTENTS) | {"expediente_siniestro"}
# Intents that the network analyst owns.
_NETWORK_INTENTS = {"redes_fraude"}
# General utility intents that should not be forced through portfolio/case analysis.
_GENERAL_INTENTS = set(GENERAL_INTENTS)


class GraphTurnState(TypedDict, total=False):
    question: str
    selected_claim_id: str | None
    claim_id: str | None
    limit: int
    intent: str
    uses_documentation: bool
    domain: str
    data: Any
    source: str
    # Reducer accumulates the trace of every agent that participated in the turn.
    agents: Annotated[list[str], operator.add]


class LangGraphUnavailableError(RuntimeError):
    """Raised when LangGraph was requested but is not installed."""


def _import_langgraph():
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as exc:
        raise LangGraphUnavailableError(
            "LangGraph no esta instalado. Agrega la dependencia para activar este runtime."
        ) from exc
    return StateGraph, START, END


def _domain_for_intent(intent_name: str, uses_documentation: bool) -> str:
    if uses_documentation:
        return "docs"
    if intent_name in _GENERAL_INTENTS:
        return "general"
    if intent_name in _CASE_INTENTS:
        return "case"
    if intent_name in _NETWORK_INTENTS:
        return "network"
    return "portfolio"


@lru_cache(maxsize=1)
def _compile_graph(
    tool_dispatcher: Callable[[str, str | None, int, str], Any],
    docs_dispatcher: Callable[[str], Any],
):
    StateGraph, START, END = _import_langgraph()

    def supervisor_node(state: GraphTurnState) -> GraphTurnState:
        resolved_intent = state.get("intent")
        if resolved_intent:
            uses_documentation = bool(state.get("uses_documentation"))
            domain = _domain_for_intent(resolved_intent, uses_documentation)
            return {
                "intent": resolved_intent,
                "uses_documentation": uses_documentation,
                "domain": domain,
                "agents": ["Supervisor"],
            }

        intent = route(state["question"])
        domain = _domain_for_intent(intent.name, intent.uses_documentation)
        return {
            "intent": intent.name,
            "uses_documentation": intent.uses_documentation,
            "domain": domain,
            "agents": ["Supervisor"],
        }

    def _dispatch(state: GraphTurnState) -> Any:
        return tool_dispatcher(
            state["intent"],
            state.get("claim_id"),
            state.get("limit", 10),
            state["question"],
        )

    def portfolio_analyst_node(state: GraphTurnState) -> GraphTurnState:
        return {"data": _dispatch(state), "source": "tools", "agents": ["Analista de portafolio"]}

    def case_investigator_node(state: GraphTurnState) -> GraphTurnState:
        return {"data": _dispatch(state), "source": "tools", "agents": ["Investigador de caso"]}

    def network_analyst_node(state: GraphTurnState) -> GraphTurnState:
        return {"data": _dispatch(state), "source": "tools", "agents": ["Analista de red"]}

    def docs_specialist_node(state: GraphTurnState) -> GraphTurnState:
        return {"data": docs_dispatcher(state["question"]), "source": "rag", "agents": ["Especialista en documentación"]}

    def general_assistant_node(state: GraphTurnState) -> GraphTurnState:
        return {"data": _dispatch(state), "source": "agent", "agents": ["Asistente general"]}

    def synthesizer_node(state: GraphTurnState) -> GraphTurnState:
        # Consolidation point. Data contract is preserved; we only record that
        # the synthesizer closed the turn so the trace is complete.
        return {"agents": ["Sintetizador"]}

    graph = StateGraph(GraphTurnState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("portfolio_analyst", portfolio_analyst_node)
    graph.add_node("case_investigator", case_investigator_node)
    graph.add_node("network_analyst", network_analyst_node)
    graph.add_node("docs_specialist", docs_specialist_node)
    graph.add_node("general_assistant", general_assistant_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state.get("domain", "portfolio"),
        {
            "portfolio": "portfolio_analyst",
            "case": "case_investigator",
            "network": "network_analyst",
            "docs": "docs_specialist",
            "general": "general_assistant",
        },
    )
    for specialist in ("portfolio_analyst", "case_investigator", "network_analyst", "docs_specialist", "general_assistant"):
        graph.add_edge(specialist, "synthesizer")
    graph.add_edge("synthesizer", END)
    return graph.compile()


def run_langgraph_turn(
    *,
    question: str,
    claim_id: str | None,
    selected_claim_id: str | None,
    limit: int,
    intent_name: str | None = None,
    uses_documentation: bool | None = None,
    tool_dispatcher: Callable[[str, str | None, int, str], Any],
    docs_dispatcher: Callable[[str], Any],
) -> dict[str, Any]:
    graph = _compile_graph(tool_dispatcher, docs_dispatcher)
    initial_state: GraphTurnState = {
        "question": question,
        "claim_id": claim_id or selected_claim_id,
        "selected_claim_id": selected_claim_id,
        "limit": limit,
    }
    if intent_name:
        initial_state["intent"] = intent_name
        initial_state["uses_documentation"] = bool(uses_documentation)

    state = graph.invoke(
        initial_state
    )
    agents = state.get("agents", [])
    return {
        "intent": state["intent"],
        "data": state["data"],
        "source": state.get("source", "tools"),
        "runtime": {
            "requested": "langgraph",
            "active": "langgraph",
            "status": "ok",
            "topology": "supervisor-workers",
            "agents": agents,
        },
    }
