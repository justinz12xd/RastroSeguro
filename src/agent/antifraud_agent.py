"""Tool-backed antifraud agent facade with optional LLM conversational synthesis."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.application import risk_queries as tools
from src.agent.entities import extract_claim_id, extract_limit
from src.agent.langgraph_runtime import LangGraphUnavailableError, run_langgraph_turn
from src.infrastructure.llm import LLMRequest, build_llm_provider
from src.agent.quick_questions import get_quick_questions
from src.agent.rag import search_docs
from src.agent.intents import CLAIM_REQUIRED_INTENTS, DOC_INTENTS, GENERAL_INTENTS, IntentMatch
from src.agent.responses import error, success
from src.agent.router import route


DEFAULT_TIMEZONE = "America/Guayaquil"
DIRECT_RESPONSE_INTENTS = set(GENERAL_INTENTS)
SPANISH_WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
SPANISH_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def answer_question(
    question: str,
    history: Any = None,
    *,
    selected_claim_id: str | None = None,
    thread_id: str | None = None,
    runtime: str | None = None,
    user_role: str = "analyst",
) -> dict[str, Any]:
    """Process user queries through deterministic tools and optional OpenAI synthesis."""
    # Multi-agent (LangGraph) is the default runtime. RASTRO_AGENT_RUNTIME acts as
    # an ops kill-switch that wins over the request (set it to "classic" to disable).
    env_runtime = os.environ.get("RASTRO_AGENT_RUNTIME")
    requested_runtime = (env_runtime or runtime or "langgraph").lower()
    limit = extract_limit(question)
    execution = _execute_turn(
        question,
        history=history,
        selected_claim_id=selected_claim_id,
        requested_runtime=requested_runtime,
        limit=limit,
    )
    if execution.get("ok") is False:
        return execution

    intent_name = execution["intent"]
    data = execution["data"]
    source = execution["source"]
    claim_id = execution.get("claim_id")

    base_metadata = {
        "runtime": execution["runtime"],
        "context": {
            "thread_id": thread_id,
            "selected_claim_id": selected_claim_id,
            "resolved_claim_id": claim_id,
            "user_role": user_role,
        },
    }
    if intent_name in DIRECT_RESPONSE_INTENTS:
        return success(
            intent_name,
            direct_message_for_intent(intent_name, data),
            data,
            source=source,
            metadata={
                "llm": {
                    "enabled": False,
                    "provider": "agent",
                    "model": None,
                    "status": "bypassed_for_direct_intent",
                },
                **base_metadata,
            },
        )

    llm_result = build_llm_provider().generate(
        LLMRequest(intent=intent_name, data=data, question=question, history=history, user_role=user_role)
    )
    metadata = {
        "llm": llm_result.metadata(),
        **base_metadata,
    }
    if llm_result.has_message:
        return success(intent_name, llm_result.message or "", data, source="llm", metadata=metadata)

    return success(
        intent_name,
        message_for_intent(intent_name, user_role=user_role),
        data,
        source=source,
        metadata=metadata,
    )


def dispatch_intent(intent: str, claim_id: str | None, limit: int, question: str) -> Any:
    if intent == "fecha_actual":
        return _current_date_payload()
    if intent == "saludo":
        return {
            "acciones_sugeridas": [
                "Priorizar los siniestros con mayor riesgo.",
                "Explicar por qué un siniestro fue marcado.",
                "Revisar documentos faltantes o proveedores con más alertas.",
            ]
        }
    if intent == "ayuda_agente":
        return {
            "preguntas_utiles": [
                "¿Cuáles son los 10 siniestros con mayor riesgo?",
                "¿Por qué el siniestro SIN-000678 fue marcado como alto riesgo?",
                "¿Qué proveedores concentran más alertas?",
                "¿Qué documentos faltan en los casos críticos?",
            ]
        }
    if intent == "ranking_proveedores":
        return tools.get_provider_risk_ranking(limit=limit)
    if intent == "ranking_ciudades":
        return tools.get_city_risk_distribution()
    if intent == "riesgo_por_ramo":
        return tools.get_risk_by_branch()
    if intent == "documentos_faltantes":
        return tools.get_missing_documents()
    if intent == "resumen_ejecutivo":
        return tools.generate_executive_summary()
    if intent == "casos_estrella":
        return tools.get_demo_star_cases()
    if intent == "impacto_negocio":
        return tools.get_business_impact()
    if intent == "explicar_siniestro":
        return tools.explain_claim(claim_id or "")
    if intent == "expediente_siniestro":
        return tools.get_claim_dossier(claim_id or "")
    if intent == "narrativas_similares":
        return tools.get_similar_narratives(claim_id or "")
    if intent == "conexiones_grafo":
        return tools.get_graph_connections(claim_id or "")
    if intent == "redes_fraude":
        return tools.get_fraud_rings(limit=limit)
    if intent == "simular_siniestro":
        return error(intent, "Para simular necesito recibir los datos del nuevo siniestro desde el formulario de Justin.")
    if intent == "documentacion":
        return search_docs(question)
    if intent == "recomendar_revision":
        return tools.recommend_review_order(limit=limit)
    if intent == "frecuencia_asegurados":
        return tools.get_insured_claim_frequency(limit=limit)
    if intent == "montos_atipicos":
        return tools.get_atypical_amount_claims(limit=limit)
    if intent == "borde_vigencia":
        return tools.get_policy_start_border_cases(limit=limit)
    if intent == "patrones_repetidos":
        return tools.get_repeated_patterns(limit=limit)
    if intent == "concentracion_rojos":
        return tools.get_provider_red_concentration(threshold=0.8)
    if intent == "ahorro_potencial":
        return tools.simulate_portfolio_savings()
    return tools.get_top_risky_claims(limit=limit)


def message_for_intent(intent: str, user_role: str = "analyst") -> str:
    messages = {
        "top_riesgo": "Casos priorizados por mayor score de riesgo.",
        "fecha_actual": "Fecha actual calculada con la zona horaria configurada.",
        "saludo": "Hola. Soy el asistente de RastroSeguro para priorizar y explicar riesgos antifraude.",
        "ayuda_agente": "Puedo ayudarte a priorizar casos, explicar siniestros, revisar documentos y encontrar concentraciones de riesgo.",
        "ranking_proveedores": "Ranking de proveedores por concentracion de riesgo.",
        "ranking_ciudades": "Distribucion de riesgo por ciudad.",
        "riesgo_por_ramo": "Comparacion de riesgo por ramo.",
        "documentos_faltantes": "Casos con documentos faltantes o incompletos.",
        "resumen_ejecutivo": "Resumen ejecutivo generado desde datos procesados.",
        "casos_estrella": "Casos estrella seleccionados para demo ejecutiva.",
        "impacto_negocio": "Impacto de priorizacion expresado como exposicion a revisar, no ahorro automatico.",
        "explicar_siniestro": "Explicacion trazable del siniestro solicitado.",
        "expediente_siniestro": "Expediente antifraude con evidencias, proximos pasos y guardrail etico.",
        "narrativas_similares": "Narrativas similares detectadas para el siniestro solicitado.",
        "conexiones_grafo": "Conexiones y entidades recurrentes del siniestro solicitado.",
        "redes_fraude": "Redes o anillos de fraude detectados por entidades de riesgo compartidas.",
        "documentacion": "Respuesta basada en documentacion interna del proyecto.",
        "recomendar_revision": "Casos recomendados para revision prioritaria.",
        "frecuencia_asegurados": "Asegurados con mayor frecuencia de reclamos.",
        "montos_atipicos": "Casos con montos atipicos frente a la suma asegurada.",
        "borde_vigencia": "Siniestros ocurridos cerca del inicio de la poliza.",
        "patrones_repetidos": "Patrones recurrentes en reclamos sospechosos.",
        "concentracion_rojos": "Proveedores que concentran la mayoria de alertas rojas.",
        "ahorro_potencial": "Estimacion de ahorro potencial por revision temprana de casos rojos.",
    }
    message = messages.get(intent, "Respuesta generada desde herramientas verificables.")
    if user_role == "executive":
        executive_messages = {
            "top_riesgo": "Vista ejecutiva de casos priorizados por exposición y riesgo.",
            "ranking_proveedores": "Vista ejecutiva de proveedores con mayor concentración de alertas.",
            "riesgo_por_ramo": "Vista ejecutiva de exposición por ramo y concentración de riesgo.",
            "resumen_ejecutivo": "Resumen ejecutivo generado desde datos procesados del portafolio.",
            "impacto_negocio": "Impacto de negocio estimado para apoyar decisiones de priorización.",
            "casos_estrella": "Casos seleccionados para demostración ejecutiva y toma de decisiones.",
        }
        return executive_messages.get(intent, message)
    return message


def _recover_claim_id_from_history(history: Any) -> str | None:
    if not history:
        return None
    for turn in reversed(list(history)):
        content = turn.get("content") if isinstance(turn, dict) else getattr(turn, "content", "")
        recovered = extract_claim_id(content or "")
        if recovered:
            return recovered
    return None


def _execute_turn(
    question: str,
    *,
    history: Any,
    selected_claim_id: str | None,
    requested_runtime: str,
    limit: int,
) -> dict[str, Any]:
    intent = route(question)
    claim_id = extract_claim_id(question) or selected_claim_id or _recover_claim_id_from_history(history)

    # When a claim is in focus and the router fell back to the generic default
    # (no alias matched -> confidence 0.35), only treat the turn as claim-scoped
    # if the wording actually looks like a follow-up about the selected claim.
    if (
        selected_claim_id
        and intent.name == "top_riesgo"
        and intent.confidence <= 0.35
        and _looks_like_claim_follow_up(question)
    ):
        intent = IntentMatch(
            name="explicar_siniestro",
            confidence=0.5,
            requires_claim_id="explicar_siniestro" in CLAIM_REQUIRED_INTENTS,
            uses_documentation="explicar_siniestro" in DOC_INTENTS,
        )

    if intent.requires_claim_id and not claim_id:
        return error(
            intent.name,
            "Necesito el id del siniestro para responder esa pregunta.",
            "Ejemplo: Explicame el siniestro SIN-0045.",
        )

    runtime_metadata = {
        "requested": requested_runtime,
        "active": "classic",
        "status": "ok",
    }

    try:
        if requested_runtime == "langgraph":
            graph_turn = run_langgraph_turn(
                question=question,
                claim_id=claim_id,
                selected_claim_id=selected_claim_id,
                limit=limit,
                intent_name=intent.name,
                uses_documentation=intent.uses_documentation,
                tool_dispatcher=dispatch_intent,
                docs_dispatcher=search_docs,
            )
            return {
                "ok": True,
                "intent": graph_turn["intent"],
                "data": graph_turn["data"],
                "source": graph_turn["source"],
                "claim_id": claim_id,
                "runtime": graph_turn["runtime"],
            }

        data = dispatch_intent(intent.name, claim_id=claim_id, limit=limit, question=question)
        return {
            "ok": True,
            "intent": intent.name,
            "data": data,
            "source": _source_for_intent(intent.name, intent.uses_documentation),
            "claim_id": claim_id,
            "runtime": runtime_metadata,
        }
    except LangGraphUnavailableError as exc:
        data = dispatch_intent(intent.name, claim_id=claim_id, limit=limit, question=question)
        runtime_metadata["status"] = "langgraph_not_installed"
        runtime_metadata["detail"] = str(exc)
        return {
            "ok": True,
            "intent": intent.name,
            "data": data,
            "source": _source_for_intent(intent.name, intent.uses_documentation),
            "claim_id": claim_id,
            "runtime": runtime_metadata,
        }
    except FileNotFoundError as exc:
        return error(intent.name, str(exc), "Ejecuta primero el scoring para generar data/processed/siniestros_scored.csv.")
    except ValueError as exc:
        return error(intent.name, str(exc))


def direct_message_for_intent(intent: str, data: Any) -> str:
    if intent == "fecha_actual" and isinstance(data, dict):
        return _format_current_date_message(data)
    if intent == "saludo":
        return "Hola. Soy el asistente de RastroSeguro. Puedo ayudarte a priorizar casos, explicar un siniestro o revisar señales antifraude."
    if intent == "ayuda_agente":
        return "Puedes pedirme rankings de riesgo, explicación de un siniestro, documentos faltantes, proveedores con alertas o un resumen ejecutivo."
    return message_for_intent(intent)


def _current_date_payload(tz_name: str | None = None) -> dict[str, Any]:
    resolved_tz = tz_name or os.environ.get("RASTRO_AGENT_TIMEZONE", DEFAULT_TIMEZONE)
    now = _now_in_timezone(resolved_tz)
    return {
        "fecha_iso": now.date().isoformat(),
        "dia_semana": SPANISH_WEEKDAYS[now.weekday()],
        "dia": now.day,
        "mes": SPANISH_MONTHS[now.month - 1],
        "anio": now.year,
        "zona_horaria": resolved_tz,
    }


def _now_in_timezone(tz_name: str) -> datetime:
    return datetime.now(_resolve_timezone(tz_name))


def _resolve_timezone(tz_name: str) -> tzinfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        if tz_name == DEFAULT_TIMEZONE:
            return timezone(timedelta(hours=-5), DEFAULT_TIMEZONE)
        return timezone.utc


def _format_current_date_message(data: dict[str, Any]) -> str:
    return (
        f"Hoy es {data.get('dia_semana')}, {data.get('dia')} de {data.get('mes')} "
        f"de {data.get('anio')} ({data.get('zona_horaria')})."
    )


def _looks_like_claim_follow_up(question: str) -> bool:
    text = question.lower()
    phrase_markers = (
        "que paso",
        "qué pasó",
        "que hago",
        "qué hago",
        "que sigue",
        "qué sigue",
        "siguiente paso",
        "del caso",
        "del siniestro",
        "explicalo",
        "explícalo",
        "resumelo",
        "resúmelo",
        "dime mas",
        "dime más",
        "por que",
        "por qué",
    )
    word_markers = ("aqui", "aquí", "este", "esta", "esto")
    return any(marker in text for marker in phrase_markers) or any(
        re.search(rf"\b{re.escape(marker)}\b", text) for marker in word_markers
    )


def _source_for_intent(intent: str, uses_documentation: bool) -> str:
    if intent in GENERAL_INTENTS:
        return "agent"
    return "rag" if uses_documentation else "tools"


__all__ = ["answer_question", "dispatch_intent", "get_quick_questions", "message_for_intent"]
