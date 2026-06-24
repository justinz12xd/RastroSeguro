"""Response shaping for simulator UI/demo consumption."""

from __future__ import annotations

from typing import Any


def build_simulation_response(
    explanation: dict[str, Any],
    enriched_claim: dict[str, Any],
    normalized_input: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Return a backward-compatible explanation plus rich UI sections."""
    response = dict(explanation)
    response.update({
        "ok": True,
        "simulated": True,
        "source": "simulator",
        "input_normalizado": normalized_input,
        "risk": _risk_section(explanation),
        "signals": _signals_section(explanation, enriched_claim),
        "ui": _ui_section(explanation),
        "context": context,
    })
    return response


def _risk_section(explanation: dict[str, Any]) -> dict[str, Any]:
    return {
        "score_final": explanation.get("score_final"),
        "nivel_riesgo": explanation.get("nivel_riesgo"),
        "accion_sugerida": explanation.get("accion_sugerida"),
    }


def _signals_section(explanation: dict[str, Any], enriched_claim: dict[str, Any]) -> dict[str, Any]:
    advanced = explanation.get("detalles_avanzados", {}) or {}
    return {
        "rules": explanation.get("alertas", []),
        "nlp": advanced.get("nlp", {}),
        "graph": advanced.get("grafo", {}),
        "categorical": advanced.get("categorico", {}),
        "model": {
            "modelo_disponible": enriched_claim.get("modelo_disponible", False),
            "anomalia_disponible": enriched_claim.get("anomalia_disponible", False),
            "score_modelo": explanation.get("componentes_score", {}).get("modelo"),
            "score_anomalia": explanation.get("componentes_score", {}).get("anomalia"),
        },
    }


def _ui_section(explanation: dict[str, Any]) -> dict[str, Any]:
    level = explanation.get("nivel_riesgo", "Sin clasificar")
    score = explanation.get("score_final", 0)
    return {
        "priority_badge": level,
        "summary_cards": [
            {"label": "Score final", "value": score},
            {"label": "Nivel", "value": level},
            {"label": "Alertas", "value": len(explanation.get("alertas", []))},
        ],
        "recommended_next_steps": _next_steps(level),
    }


def _next_steps(level: str) -> list[str]:
    if level == "Rojo":
        return [
            "Enviar a revisión especializada.",
            "Validar documentos y evidencia del siniestro.",
            "Revisar conexiones con proveedor, vehículo, conductor o beneficiario.",
        ]
    if level == "Amarillo":
        return [
            "Solicitar revisión documental.",
            "Comparar narrativa y proveedor contra históricos.",
        ]
    return ["Continuar flujo normal con monitoreo habitual."]
