"""Graph/relationship scoring for claims."""

from __future__ import annotations

from typing import Any

from src.graph.entity_extraction import RISK_ENTITY_TYPES, graph_connections
from src.graph.relationship_metrics import build_entity_counts, recurring_entities

ENTITY_WEIGHTS = {
    "proveedor": 14,
    "beneficiario": 12,
    "vehiculo": 10,
    "taller": 10,
    "conductor": 12,
    "intermediario": 10,
    "asegurado": 6,
    "ciudad": 2,
    "ramo": 0,
    "cobertura": 1,
}


def recurrence_points(entity: dict[str, Any]) -> int:
    count = int(entity.get("total_siniestros", 0))
    base = ENTITY_WEIGHTS.get(str(entity.get("type")), 3)
    if count >= 5:
        return base
    if count >= 3:
        return max(3, int(base * 0.7))
    if count >= 2:
        return max(1, int(base * 0.4))
    return 0


def build_graph_signal(claim: dict[str, Any], recurring: list[dict[str, Any]]) -> dict[str, Any]:
    relevant = [entity for entity in recurring if entity.get("type") in RISK_ENTITY_TYPES]
    points = sum(recurrence_points(entity) for entity in relevant)
    score = min(100, round((points / 35) * 100, 2))

    if not relevant:
        explanation = "No se detectaron entidades críticas recurrentes para este siniestro."
    else:
        top = relevant[0]
        explanation = (
            f"Se detectó recurrencia en {top['type']} {top['value']} "
            f"asociado a {top['total_siniestros']} siniestros."
        )

    return {
        "id_siniestro": claim.get("id_siniestro"),
        "score_grafo": score,
        "alerta_red": bool(relevant),
        "entidades_recurrentes": relevant,
        "conexiones_grafo": graph_connections(claim),
        "explicacion_grafo": explanation,
        "proveedor_recurrente": any(entity.get("type") == "proveedor" for entity in relevant),
        "beneficiario_recurrente": any(entity.get("type") == "beneficiario" for entity in relevant),
    }


def score_relationships(claims: list[dict[str, Any]], min_count: int = 2) -> dict[str, dict[str, Any]]:
    counts, claims_by_entity = build_entity_counts(claims)
    signals: dict[str, dict[str, Any]] = {}
    for claim in claims:
        claim_id = str(claim.get("id_siniestro"))
        recurring = recurring_entities(claim, counts, claims_by_entity, min_count=min_count)
        signals[claim_id] = build_graph_signal(claim, recurring)
    return signals


def enrich_claims_with_graph(claims: list[dict[str, Any]], min_count: int = 2) -> list[dict[str, Any]]:
    signals = score_relationships(claims, min_count=min_count)
    enriched: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = str(claim.get("id_siniestro"))
        enriched_claim = dict(claim)
        if claim_id in signals:
            enriched_claim.update(signals[claim_id])
        enriched.append(enriched_claim)
    return enriched
