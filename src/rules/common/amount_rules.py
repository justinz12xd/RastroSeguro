"""Common amount risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.common.coercion import as_number
from src.rules.models import RuleResult

Claim = dict[str, Any]


def evaluate_amount_rules(claim: Claim) -> list[RuleResult]:
    amount = as_number(claim.get("monto_reclamado"))
    insured_sum = as_number(claim.get("suma_asegurada"))
    ratio = claim.get("ratio_monto_suma_asegurada")
    ratio = as_number(ratio, amount / insured_sum if insured_sum else 0)

    if ratio >= 0.95:
        return [_amount_ratio_result("RB-004", "Monto cercano a suma asegurada", 7, "alta", amount, insured_sum, ratio)]
    if ratio >= 0.80:
        return [_amount_ratio_result("RB-005", "Monto elevado frente a suma asegurada", 4, "media", amount, insured_sum, ratio)]
    return []


def _amount_ratio_result(code: str, name: str, points: int, severity: str, amount: float, insured_sum: float, ratio: float) -> RuleResult:
    return RuleResult(
        code=code,
        name=name,
        points=points,
        severity=severity,  # type: ignore[arg-type]
        message=f"El monto reclamado representa el {ratio:.0%} de la suma asegurada.",
        evidence={"monto_reclamado": amount, "suma_asegurada": insured_sum, "ratio": round(ratio, 4)},
        category="monto",
    )
