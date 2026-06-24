"""Interpretable categorical scoring."""

from __future__ import annotations

from typing import Any

from src.categorical.profiles import CategorySignal, evaluate_configured_categories


def category_score(signals: list[CategorySignal]) -> float:
    points = sum(signal.points for signal in signals)
    return round(min(100.0, (points / 30.0) * 100.0), 2)


def build_categorical_signal(claim: dict[str, Any]) -> dict[str, Any]:
    signals = evaluate_configured_categories(claim)
    serialized = [signal.to_dict() for signal in signals]

    if not signals:
        explanation = "No se detectaron categorías con riesgo adicional relevante."
    else:
        top = sorted(signals, key=lambda signal: signal.points, reverse=True)[0]
        explanation = f"La categoría '{top.field}' aporta riesgo adicional: {top.message}"

    return {
        "id_siniestro": claim.get("id_siniestro"),
        "score_categorico": category_score(signals),
        "alerta_categorica": bool(signals),
        "senales_categoricas": serialized,
        "explicacion_categorica": explanation,
    }


def enrich_claims_with_categorical(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for claim in claims:
        enriched_claim = dict(claim)
        enriched_claim.update(build_categorical_signal(claim))
        enriched.append(enriched_claim)
    return enriched
