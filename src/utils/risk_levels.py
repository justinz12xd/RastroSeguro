"""Risk level mapping and recommended actions."""

from __future__ import annotations


def clamp_score(value: float | int | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, float(value)))


def risk_level(score: float | int | None) -> str:
    score = clamp_score(score)
    if score <= 40:
        return "Verde"
    if score <= 75:
        return "Amarillo"
    return "Rojo"


def suggested_action(level: str) -> str:
    actions = {
        "Verde": "Continuar flujo normal con controles habituales.",
        "Amarillo": "Solicitar revisión documental antes de continuar el flujo.",
        "Rojo": "Escalar a revisión antifraude especializada antes de continuar el flujo.",
    }
    return actions.get(level, "Revisar el caso con un analista responsable.")
