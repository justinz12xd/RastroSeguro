"""Fraud ring detection via connected components over shared risk entities."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.graph.entity_extraction import RISK_ENTITY_TYPES, extract_entities
from src.graph.relationship_metrics import build_entity_counts


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, node: str) -> None:
        if node not in self.parent:
            self.parent[node] = node

    def find(self, node: str) -> str:
        self.add(node)
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def _is_red(level: Any) -> bool:
    return str(level or "").strip().lower() in {"rojo", "alto", "critico", "crítico", "critical", "high"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _ring_risk_score(tamano: int, casos_rojos: int, entidades_compartidas: int, score_promedio: float) -> float:
    size_pts = min(40.0, tamano * 8.0)
    red_pts = min(30.0, (casos_rojos / max(tamano, 1)) * 30.0)
    entity_pts = min(20.0, entidades_compartidas * 5.0)
    score_pts = min(10.0, score_promedio / 10.0)
    return round(min(100.0, size_pts + red_pts + entity_pts + score_pts), 2)


def _build_explicacion(
    tamano: int,
    casos_rojos: int,
    monto_expuesto: float,
    entidades: list[dict[str, Any]],
) -> str:
    if not entidades:
        entity_text = "entidades de riesgo compartidas"
    else:
        labels = [f"{item['type']} {item['value']}" for item in entidades[:3]]
        entity_text = ", ".join(labels)
    return (
        f"Anillo de {tamano} siniestros unidos por {entity_text}; "
        f"{casos_rojos} caso(s) rojo(s); exposición priorizada ${monto_expuesto:,.0f}. "
        "Señal de red para revisión humana, no acusación automática."
    )


def detect_fraud_rings(
    claims: list[dict[str, Any]],
    *,
    min_size: int = 2,
    limit: int = 10,
) -> dict[str, Any]:
    """Detect fraud rings as connected components sharing risk entity keys."""
    if not claims:
        return {"total_anillos": 0, "anillos": [], "explicacion_global": "No hay siniestros para analizar redes."}

    claims_by_id: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims):
        claim_id = str(claim.get("id_siniestro", f"ROW-{index}"))
        claims_by_id[claim_id] = claim

    _counts, claims_by_entity = build_entity_counts(claims)
    uf = _UnionFind()

    for claim_id in claims_by_id:
        uf.add(claim_id)

    for entity_key, linked_claims in claims_by_entity.items():
        entity_type = entity_key.split(":", 1)[0]
        if entity_type not in RISK_ENTITY_TYPES:
            continue
        linked = sorted(linked_claims)
        if len(linked) < 2:
            continue
        anchor = linked[0]
        for other in linked[1:]:
            uf.union(anchor, other)

    components: dict[str, list[str]] = defaultdict(list)
    for claim_id in claims_by_id:
        components[uf.find(claim_id)].append(claim_id)

    rings: list[dict[str, Any]] = []
    ring_index = 0

    for members in components.values():
        if len(members) < min_size:
            continue
        ring_index += 1
        members_sorted = sorted(members)
        ring_claims = [claims_by_id[cid] for cid in members_sorted]

        entity_claim_map: dict[str, set[str]] = defaultdict(set)
        for claim in ring_claims:
            claim_id = str(claim.get("id_siniestro"))
            seen: set[str] = set()
            for entity in extract_entities(claim):
                if entity.entity_type not in RISK_ENTITY_TYPES:
                    continue
                if entity.key in seen:
                    continue
                seen.add(entity.key)
                entity_claim_map[entity.key].add(claim_id)

        entidades_compartidas = [
            {
                "type": key.split(":", 1)[0],
                "value": key.split(":", 1)[1] if ":" in key else key,
                "key": key,
                "siniestros_vinculados": len(linked),
                "siniestros_relacionados": sorted(linked)[:12],
            }
            for key, linked in sorted(
                entity_claim_map.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )
            if len(linked) >= 2
        ]

        casos_rojos = sum(1 for claim in ring_claims if _is_red(claim.get("nivel_riesgo")))
        scores = [_safe_float(claim.get("score_final")) for claim in ring_claims]
        score_promedio = round(sum(scores) / max(len(scores), 1), 2)
        monto_expuesto = round(
            sum(_safe_float(claim.get("monto_reclamado")) for claim in ring_claims),
            2,
        )
        tamano = len(members_sorted)
        ring_score = _ring_risk_score(tamano, casos_rojos, len(entidades_compartidas), score_promedio)

        rings.append(
            {
                "id_anillo": f"RING-{ring_index:03d}",
                "siniestros": members_sorted,
                "tamano": tamano,
                "casos_rojos": casos_rojos,
                "pct_rojos": round((casos_rojos / tamano) * 100, 1),
                "monto_expuesto": monto_expuesto,
                "score_promedio": score_promedio,
                "ring_risk_score": ring_score,
                "entidades_compartidas": entidades_compartidas,
                "explicacion": _build_explicacion(tamano, casos_rojos, monto_expuesto, entidades_compartidas),
                "claims_resumen": [
                    {
                        "id_siniestro": str(claim.get("id_siniestro")),
                        "ramo": claim.get("ramo"),
                        "nivel_riesgo": claim.get("nivel_riesgo"),
                        "score_final": claim.get("score_final"),
                        "monto_reclamado": claim.get("monto_reclamado"),
                        "id_proveedor": claim.get("id_proveedor"),
                        "beneficiario": claim.get("beneficiario"),
                    }
                    for claim in ring_claims
                ],
            }
        )

    rings.sort(key=lambda item: (-item["ring_risk_score"], -item["tamano"]))
    for idx, ring in enumerate(rings[:limit], start=1):
        ring["id_anillo"] = f"RING-{idx:03d}"

    limited = rings[:limit]
    if not limited:
        global_msg = "No se detectaron anillos con al menos dos siniestros conectados por entidades de riesgo."
    else:
        top = limited[0]
        global_msg = (
            f"Se detectaron {len(rings)} red(es) de posible coordinación. "
            f"La de mayor riesgo ({top['id_anillo']}) agrupa {top['tamano']} siniestros "
            f"con score de red {top['ring_risk_score']}/100."
        )

    return {
        "total_anillos": len(rings),
        "anillos": limited,
        "explicacion_global": global_msg,
    }


def detect_fraud_rings_from_records(
    records: list[dict[str, Any]],
    *,
    min_size: int = 2,
    limit: int = 10,
) -> dict[str, Any]:
    """Alias for detect_fraud_rings used by agent tools."""
    return detect_fraud_rings(records, min_size=min_size, limit=limit)


__all__ = ["detect_fraud_rings", "detect_fraud_rings_from_records"]
