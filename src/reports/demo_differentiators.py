"""Demo differentiators for the hackIAthon pitch.

These helpers turn the scored CSV into juror-friendly artifacts: a claim dossier,
star cases, a simple relationship network and business-impact figures. They are
intentionally deterministic and data-backed so the agent/UI can cite evidence
instead of producing generic chatbot text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.scoring.final_score import OUTPUT_PATH
from src.utils.serialization import from_json_list


def _load_scored(data_path: Path = OUTPUT_PATH):
    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró {data_path}. Ejecuta python -m src.scoring.final_score")
    import pandas as pd

    return pd.read_csv(data_path)


def _safe_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value != value:  # NaN check
            return default
        return float(value)
    except Exception:
        return default


def _record_for_claim(id_siniestro: str, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    df = _load_scored(data_path)
    matches = df[df["id_siniestro"].astype(str) == str(id_siniestro)]
    if matches.empty:
        raise ValueError(f"No se encontró el siniestro {id_siniestro} en {data_path}.")
    return matches.iloc[0].to_dict()


def _clean_text(value: Any, fallback: str = "No informado") -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return fallback
    return text


def _format_day(value: Any) -> str | None:
    text = _clean_text(value, "")
    return text or None


def _risk_phrase(level: str) -> str:
    if level == "Rojo":
        return "prioridad crítica para revisión especializada"
    if level == "Amarillo":
        return "prioridad media con validación documental recomendada"
    if level == "Verde":
        return "monitoreo habitual con bajo nivel de alerta"
    return "prioridad pendiente de clasificación"


def _build_investigation_summary(row: dict[str, Any], level: str, evidence: list[dict[str, Any]], top_component: tuple[str, float]) -> str:
    claim_id = _clean_text(row.get("id_siniestro"), "Este siniestro")
    branch = _clean_text(row.get("ramo"), "ramo no informado")
    city = _clean_text(row.get("ciudad"), "ciudad no informada")
    amount = _safe_number(row.get("monto_reclamado"))
    top_signal = evidence[0].get("senal") if evidence else top_component[0]
    return (
        f"RastroSeguro reconstruyó {claim_id} como un caso de {_risk_phrase(level)}. "
        f"El reclamo de {branch} en {city} concentra una exposición de ${amount:,.0f} "
        f"y su señal dominante es {top_signal}. La recomendación es priorizar revisión humana "
        "con evidencia trazable, sin acusación ni decisión automática."
    )


def _build_timeline(row: dict[str, Any], level: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    days_from_start = _safe_number(row.get("dias_desde_inicio_poliza"), -1)
    report_delay = _safe_number(row.get("dias_entre_ocurrencia_reporte"), -1)
    docs_complete = str(row.get("documentos_completos", "")).lower() in {"true", "1", "si", "sí", "yes"}
    docs_inconsistent = str(row.get("documentos_inconsistentes", "")).lower() in {"true", "1", "si", "sí", "yes"}
    score = round(_safe_number(row.get("score_final")), 2)
    timeline = [
        {
            "title": "Inicio de póliza",
            "date": "Día 0",
            "detail": (
                f"El siniestro ocurre {int(days_from_start)} día(s) después del inicio."
                if days_from_start >= 0
                else "Fecha base no disponible; se mantiene trazabilidad con datos del reclamo."
            ),
            "tone": "neutral",
        },
        {
            "title": "Ocurrencia del siniestro",
            "date": _format_day(row.get("fecha_ocurrencia")) or "Fecha no informada",
            "detail": f"Ramo {_clean_text(row.get('ramo'))} · Ciudad {_clean_text(row.get('ciudad'))}.",
            "tone": "info",
        },
        {
            "title": "Reporte del siniestro",
            "date": _format_day(row.get("fecha_reporte")) or "Fecha no informada",
            "detail": (
                f"Reporte registrado {int(report_delay)} día(s) después de la ocurrencia."
                if report_delay >= 0
                else "Brecha ocurrencia-reporte no disponible."
            ),
            "tone": "info",
        },
        {
            "title": "Validación documental",
            "date": "Control de integridad",
            "detail": (
                "Documentación con inconsistencias detectadas."
                if docs_inconsistent
                else "Documentación completa reportada." if docs_complete else "Documentación requiere validación manual."
            ),
            "tone": "warning" if docs_inconsistent or not docs_complete else "success",
        },
        {
            "title": "Evaluación IA",
            "date": f"Score {score}/100",
            "detail": f"Nivel {level}. {len(evidence)} señal(es) trazables incluidas en el expediente.",
            "tone": "critical" if level == "Rojo" else "warning" if level == "Amarillo" else "success",
        },
        {
            "title": "Recomendación humana",
            "date": "Sin decisión automática",
            "detail": _clean_text(row.get("accion_sugerida"), "Revisión humana según protocolo de riesgo."),
            "tone": "neutral",
        },
    ]
    return timeline


def _build_signal_radar(components: dict[str, float]) -> list[dict[str, Any]]:
    descriptions = {
        "Reglas": "Señales auditables de negocio y vigencia.",
        "Modelo ML": "Patrones aprendidos desde variables del portafolio.",
        "Anomalías": "Desviaciones frente al comportamiento esperado.",
        "NLP": "Narrativa, similitud textual y señales semánticas.",
        "Grafo": "Relaciones con entidades o casos recurrentes.",
        "Categórico": "Perfil de ramo, ciudad y cobertura.",
    }
    radar = []
    for component, value in components.items():
        score = round(_safe_number(value), 2)
        if score >= 75:
            label = "Señal dominante"
        elif score >= 55:
            label = "Señal relevante"
        elif score > 0:
            label = "Señal de apoyo"
        else:
            label = "Sin aporte"
        radar.append({
            "component": component,
            "score": score,
            "label": label,
            "description": descriptions.get(component, "Componente de riesgo."),
        })
    return sorted(radar, key=lambda item: item["score"], reverse=True)


def _build_similar_cases_summary(similar: list[dict[str, Any]], connections: list[dict[str, Any]], recurring: list[dict[str, Any]]) -> dict[str, Any]:
    top_similar = []
    for item in similar[:4]:
        similarity = _safe_number(item.get("similaridad") or item.get("similarity") or item.get("score"))
        top_similar.append({
            "id_siniestro": item.get("id_siniestro") or item.get("id") or item.get("claim_id") or "Caso relacionado",
            "similarity": round(similarity * 100 if similarity <= 1 else similarity, 1),
            "reason": item.get("motivo") or item.get("reason") or "Narrativa o patrón operativo comparable.",
        })
    entities = []
    for item in recurring[:4]:
        entities.append({
            "entity": item.get("entity") or item.get("entidad") or item.get("id") or "Entidad recurrente",
            "type": item.get("type") or item.get("tipo") or "relación",
            "count": int(_safe_number(item.get("count") or item.get("conteo"), 0)),
        })
    return {
        "headline": (
            f"{len(top_similar)} caso(s) similar(es) y {len(entities)} entidad(es) recurrente(s) detectadas."
            if top_similar or entities or connections
            else "Sin casos similares o relaciones recurrentes relevantes en los datos actuales."
        ),
        "similar_cases": top_similar,
        "recurring_entities": entities,
        "connections_count": len(connections),
    }


def build_claim_dossier(id_siniestro: str, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Build an investigation-style dossier for one claim.

    The output is designed for the UI and agent: clear evidence, score components,
    recommended next steps and ethical guardrails.
    """
    row = _record_for_claim(id_siniestro, data_path=data_path)
    alerts = sorted(from_json_list(row.get("alertas_activadas")), key=lambda a: _safe_number(a.get("points")), reverse=True)
    components = {
        "Reglas": _safe_number(row.get("score_reglas")),
        "Modelo ML": _safe_number(row.get("score_modelo")),
        "Anomalías": _safe_number(row.get("score_anomalia")),
        "NLP": _safe_number(row.get("score_nlp")),
        "Grafo": _safe_number(row.get("score_grafo")),
        "Categórico": _safe_number(row.get("score_categorico")),
    }
    top_component = max(components.items(), key=lambda item: item[1])
    evidence = []
    for alert in alerts[:6]:
        evidence.append({
            "codigo": alert.get("code"),
            "senal": alert.get("name"),
            "puntos": _safe_number(alert.get("points")),
            "severidad": alert.get("severity"),
            "mensaje": alert.get("message"),
            "evidencia": alert.get("evidence", {}),
        })

    similar = from_json_list(row.get("siniestros_similares"))[:5]
    connections = from_json_list(row.get("conexiones_grafo"))[:8]
    recurring = from_json_list(row.get("entidades_recurrentes"))[:8]
    ratio = _safe_number(row.get("monto_reclamado")) / max(_safe_number(row.get("suma_asegurada"), 1), 1)

    level = str(row.get("nivel_riesgo", "Sin clasificar"))
    investigation_summary = _build_investigation_summary(row, level, evidence, top_component)
    similar_cases_summary = _build_similar_cases_summary(similar, connections, recurring)
    return {
        "id_siniestro": row.get("id_siniestro"),
        "headline": f"Expediente {row.get('id_siniestro')} · {level} · {round(_safe_number(row.get('score_final')), 2)}/100",
        "risk": {
            "score_final": round(_safe_number(row.get("score_final")), 2),
            "nivel_riesgo": level,
            "accion_sugerida": row.get("accion_sugerida"),
            "decision_automatica": "No",
            "revision_humana_requerida": "Sí" if level in {"Amarillo", "Rojo"} else "Monitoreo habitual",
        },
        "claim": {
            "ramo": row.get("ramo"),
            "cobertura": row.get("cobertura"),
            "ciudad": row.get("ciudad"),
            "id_asegurado": row.get("id_asegurado"),
            "id_proveedor": row.get("id_proveedor"),
            "beneficiario": row.get("beneficiario"),
            "monto_reclamado": _safe_number(row.get("monto_reclamado")),
            "suma_asegurada": _safe_number(row.get("suma_asegurada")),
            "ratio_monto_suma": round(ratio, 4),
            "fecha_ocurrencia": row.get("fecha_ocurrencia"),
            "fecha_reporte": row.get("fecha_reporte"),
        },
        "evidence": evidence,
        "score_components": components,
        "main_driver": {"componente": top_component[0], "valor": round(top_component[1], 2)},
        "investigation_summary": investigation_summary,
        "timeline": _build_timeline(row, level, evidence),
        "signal_radar": _build_signal_radar(components),
        "similar_cases_summary": similar_cases_summary,
        "executive_takeaway": (
            f"{row.get('id_siniestro')} concentra {_risk_phrase(level)}: "
            f"score {round(_safe_number(row.get('score_final')), 2)}/100, "
            f"monto reclamado ${_safe_number(row.get('monto_reclamado')):,.0f}, "
            f"driver principal {top_component[0]}. "
            "Debe revisarse por una persona antes de cualquier decisión."
        ),
        "advanced_evidence": {
            "nlp": {
                "explicacion": row.get("explicacion_nlp", ""),
                "similares": similar,
            },
            "grafo": {
                "explicacion": row.get("explicacion_grafo", ""),
                "conexiones": connections,
                "entidades_recurrentes": recurring,
            },
        },
        "recommended_review": _review_steps(level, evidence, bool(similar), bool(connections or recurring)),
        "ethical_guardrail": "Este resultado es una alerta de priorización. No constituye acusación de fraude ni decisión automática de pago o rechazo.",
        "explanation": row.get("explicacion"),
    }


def _review_steps(level: str, evidence: list[dict[str, Any]], has_nlp: bool, has_graph: bool) -> list[str]:
    steps = []
    if level == "Rojo":
        steps.append("Escalar a unidad antifraude para revisión especializada.")
    elif level == "Amarillo":
        steps.append("Solicitar revisión documental antes de continuar el flujo normal.")
    else:
        steps.append("Continuar flujo normal y mantener monitoreo de señales futuras.")
    categories = {str(item.get("codigo", ""))[:2] for item in evidence}
    if evidence:
        steps.append("Validar las evidencias de las alertas de mayor puntaje.")
    if has_graph:
        steps.append("Revisar relaciones con proveedor, beneficiario, asegurado o vehículo recurrente.")
    if has_nlp:
        steps.append("Comparar narrativa contra reclamos similares antes de cerrar la revisión.")
    if "RB" in categories:
        steps.append("Documentar reglas activadas en el expediente para auditoría.")
    return steps[:5]


def build_business_impact(data_path: Path = OUTPUT_PATH, review_percent: float = 0.10) -> dict[str, Any]:
    """Estimate prioritization impact without claiming automatic savings."""
    df = _load_scored(data_path)
    total_claims = int(len(df))
    review_n = max(1, int(round(total_claims * review_percent))) if total_claims else 0
    ordered = df.sort_values("score_final", ascending=False).head(review_n) if total_claims else df
    amount_total = _safe_number(df.get("monto_reclamado", []).sum()) if total_claims and "monto_reclamado" in df else 0
    amount_red = _safe_number(df.loc[df["nivel_riesgo"].astype(str) == "Rojo", "monto_reclamado"].sum()) if total_claims and "monto_reclamado" in df else 0
    amount_review = _safe_number(ordered.get("monto_reclamado", []).sum()) if total_claims and "monto_reclamado" in ordered else 0
    red_cases = int((df["nivel_riesgo"].astype(str) == "Rojo").sum()) if total_claims else 0
    return {
        "total_siniestros": total_claims,
        "casos_rojos": red_cases,
        "casos_a_revisar_top_percent": review_n,
        "porcentaje_revision": round(review_percent * 100, 1),
        "monto_total_reclamado": round(amount_total, 2),
        "monto_en_casos_rojos": round(amount_red, 2),
        "monto_priorizado_top_percent": round(amount_review, 2),
        "mensaje": f"Revisando el top {round(review_percent * 100, 1)}% por riesgo se priorizan {review_n} casos y una exposición de ${amount_review:,.0f}. Es exposición priorizada, no ahorro automático.",
    }


def build_star_case_catalog(data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Select differentiated cases for the live demo narrative."""
    df = _load_scored(data_path)
    cases: list[dict[str, Any]] = []

    def add_case(kind: str, description: str, subset):
        if subset is None or subset.empty:
            return
        for _, candidate in subset.sort_values("score_final", ascending=False).iterrows():
            row = candidate.to_dict()
            if any(item["id_siniestro"] == row.get("id_siniestro") for item in cases):
                continue
            cases.append({
                "tipo": kind,
                "id_siniestro": row.get("id_siniestro"),
                "nivel_riesgo": row.get("nivel_riesgo"),
                "score_final": round(_safe_number(row.get("score_final")), 2),
                "ramo": row.get("ramo"),
                "ciudad": row.get("ciudad"),
                "id_proveedor": row.get("id_proveedor"),
                "monto_reclamado": _safe_number(row.get("monto_reclamado")),
                "por_que_destaca": description,
                "explicacion_demo": row.get("explicacion"),
            })
            return

    red = df[df["nivel_riesgo"].astype(str) == "Rojo"]
    add_case("Rojo evidente", "Muchas reglas de negocio y evidencia documental/temporal acumulada.", red)
    if {"score_reglas", "score_grafo", "score_nlp"}.issubset(df.columns):
        non_obvious = df[(df["score_reglas"] < 55) & ((df["score_grafo"] >= 60) | (df["score_nlp"] >= 60))]
        add_case("Rojo no evidente", "El riesgo emerge por narrativa, grafo o anomalía, no solo por reglas obvias.", non_obvious)
    yellow = df[df["nivel_riesgo"].astype(str) == "Amarillo"]
    add_case("Amarillo ético", "Señales moderadas: requiere revisión, no acusación ni rechazo automático.", yellow)
    if "id_proveedor" in df.columns:
        provider_counts = df.groupby("id_proveedor").size().sort_values(ascending=False)
        if not provider_counts.empty:
            recurrent_provider = provider_counts.index[0]
            add_case("Proveedor recurrente", "Muestra concentración operativa de alertas alrededor de una entidad.", df[df["id_proveedor"] == recurrent_provider])
    if "alerta_narrativa" in df.columns:
        narr = df[df["alerta_narrativa"].astype(str).str.lower().isin({"true", "1", "yes"})]
        add_case("Narrativa similar", "Permite enseñar reclamos con textos parecidos y posible patrón repetido.", narr)

    for _, row in df.sort_values("score_final", ascending=False).iterrows():
        if len(cases) >= 5:
            break
        add_case("Caso adicional", "Caso de respaldo para preguntas del jurado o contingencia de demo.", df[df["id_siniestro"] == row["id_siniestro"]])

    return {"count": len(cases), "cases": cases}
