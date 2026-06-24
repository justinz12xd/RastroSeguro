"""Report section builders from scored claims."""

from __future__ import annotations

from typing import Any


def risk_counts(claims: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"Verde": 0, "Amarillo": 0, "Rojo": 0}
    for claim in claims:
        level = str(claim.get("nivel_riesgo", ""))
        if level in counts:
            counts[level] += 1
    return counts


def top_claims(claims: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    columns = ["id_siniestro", "ramo", "ciudad", "id_proveedor", "score_final", "nivel_riesgo", "accion_sugerida"]
    sorted_claims = sorted(claims, key=lambda claim: float(claim.get("score_final", 0) or 0), reverse=True)
    return [{column: claim.get(column) for column in columns if column in claim} for claim in sorted_claims[:limit]]


def aggregate_by_field(claims: list[dict[str, Any]], field: str, limit: int = 10) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for claim in claims:
        key = str(claim.get(field, "Sin dato"))
        bucket = buckets.setdefault(key, {field: key, "total_siniestros": 0, "casos_rojos": 0, "score_total": 0.0})
        bucket["total_siniestros"] += 1
        bucket["score_total"] += float(claim.get("score_final", 0) or 0)
        if claim.get("nivel_riesgo") == "Rojo":
            bucket["casos_rojos"] += 1

    rows = []
    for bucket in buckets.values():
        total = bucket["total_siniestros"]
        rows.append({
            field: bucket[field],
            "total_siniestros": total,
            "casos_rojos": bucket["casos_rojos"],
            "score_promedio": round(bucket["score_total"] / total, 2) if total else 0,
        })
    return sorted(rows, key=lambda row: (row["casos_rojos"], row["score_promedio"]), reverse=True)[:limit]


def exposed_amount(claims: list[dict[str, Any]], level: str = "Rojo") -> float:
    return round(sum(float(claim.get("monto_reclamado", 0) or 0) for claim in claims if claim.get("nivel_riesgo") == level), 2)
