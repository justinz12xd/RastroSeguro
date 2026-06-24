"""General insurance-specific risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.base_rules import _bool, _num
from src.rules.models import RuleResult

Claim = dict[str, Any]


def evaluate_general_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []
    ramo = str(claim.get("ramo", "")).strip().lower()
    if ramo not in {"generales", "general", "otros"}:
        return results

    amount = _num(claim.get("monto_reclamado"))
    avg = _num(claim.get("monto_promedio_cobertura"), _num(claim.get("monto_estimado")))
    if avg and amount > avg * 1.75:
        results.append(RuleResult(
            code="RG-001",
            name="Monto atípico para cobertura general",
            points=7,
            severity="alta",
            message="El monto reclamado es atípico frente al promedio/estimado de la cobertura.",
            evidence={"monto_reclamado": amount, "referencia": avg, "ratio": round(amount / avg, 4)},
            category="generales",
        ))

    if _bool(claim.get("intermediario_recurrente")):
        results.append(RuleResult(
            code="RG-002",
            name="Intermediario recurrente",
            points=6,
            severity="alta",
            message="El intermediario aparece asociado a múltiples casos observados.",
            evidence={"intermediario_recurrente": claim.get("intermediario_recurrente")},
            category="generales",
        ))

    if _bool(claim.get("inconsistencia_cobertura")):
        results.append(RuleResult(
            code="RG-003",
            name="Inconsistencia entre cobertura y evento",
            points=8,
            severity="alta",
            message="Se detecta inconsistencia entre la cobertura contratada y el evento reportado.",
            evidence={"inconsistencia_cobertura": claim.get("inconsistencia_cobertura")},
            category="generales",
        ))

    return results
