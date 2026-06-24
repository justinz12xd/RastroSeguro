"""Potential savings simulation for prioritized red cases (PDF §10.2)."""

from __future__ import annotations

import os
from typing import Any


def prevention_rate() -> float:
    raw = os.getenv("RASTRO_SAVINGS_PREVENTION_RATE", "0.20")
    try:
        value = float(raw)
    except ValueError:
        value = 0.20
    return max(0.05, min(0.50, value))


def simulate_savings(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Estimate illustrative savings from early review of red cases."""
    red = [c for c in claims if str(c.get("nivel_riesgo", "")).lower() == "rojo"]
    rate = prevention_rate()
    exposed = round(sum(float(c.get("monto_reclamado", 0) or 0) for c in red), 2)
    estimated = round(exposed * rate, 2)

    by_branch: dict[str, float] = {}
    for claim in red:
        branch = str(claim.get("ramo", "otro"))
        by_branch[branch] = by_branch.get(branch, 0.0) + float(claim.get("monto_reclamado", 0) or 0)
    branch_breakdown = [
        {
            "ramo": branch,
            "monto_expuesto": round(amount, 2),
            "ahorro_estimado": round(amount * rate, 2),
        }
        for branch, amount in sorted(by_branch.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "casos_rojos": len(red),
        "monto_expuesto_rojos": exposed,
        "tasa_prevencion_asumida": rate,
        "ahorro_potencial_estimado": estimated,
        "desglose_por_ramo": branch_breakdown,
        "nota_etica": (
            "Estimación ilustrativa basada en revisión temprana de casos rojos. "
            "No representa ahorro garantizado ni una decisión automática de pago."
        ),
    }
