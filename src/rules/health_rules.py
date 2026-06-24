"""Health insurance-specific risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.base_rules import _bool, _num
from src.rules.models import RuleResult
from src.utils.dates import days_between

Claim = dict[str, Any]


def evaluate_health_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []
    ramo = str(claim.get("ramo", "")).strip().lower()
    if ramo not in {"salud", "health", "medico", "médico"}:
        return results

    amount = _num(claim.get("monto_reclamado"))
    avg = _num(claim.get("monto_promedio_procedimiento"), _num(claim.get("monto_estimado")))
    if avg and amount > avg * 1.5:
        results.append(RuleResult(
            code="RS-001",
            name="Procedimiento con monto superior al promedio",
            points=7,
            severity="alta",
            message=f"El monto reclamado supera en más de 50% el promedio/estimado del procedimiento.",
            evidence={"monto_reclamado": amount, "referencia": avg, "ratio": round(amount / avg, 4)},
            category="salud",
        ))

    frequency = int(_num(claim.get("frecuencia_atenciones")))
    if frequency >= 4:
        results.append(RuleResult(
            code="RS-002",
            name="Frecuencia atípica de atenciones",
            points=6,
            severity="alta",
            message=f"El asegurado registra {frequency} atenciones asociadas en un periodo corto.",
            evidence={"frecuencia_atenciones": frequency},
            category="salud",
        ))

    if _bool(claim.get("proveedor_medico_recurrente")) or _bool(claim.get("clinica_recurrente")):
        results.append(RuleResult(
            code="RS-003",
            name="Clínica o proveedor médico recurrente",
            points=6,
            severity="alta",
            message="La clínica/proveedor médico aparece en casos observados de riesgo.",
            evidence={
                "proveedor_medico_recurrente": claim.get("proveedor_medico_recurrente"),
                "clinica_recurrente": claim.get("clinica_recurrente"),
            },
            category="salud",
        ))

    invoice_gap = days_between(claim.get("fecha_atencion"), claim.get("fecha_factura"))
    if invoice_gap is not None and invoice_gap < 0:
        results.append(RuleResult(
            code="RS-004",
            name="Factura emitida antes de la atención",
            points=10,
            severity="critica",
            message="La fecha de factura es anterior a la fecha de atención médica.",
            evidence={"dias_entre_atencion_factura": invoice_gap},
            category="salud",
        ))
    elif invoice_gap is not None and invoice_gap > 30:
        results.append(RuleResult(
            code="RS-005",
            name="Factura emitida tardíamente",
            points=4,
            severity="media",
            message=f"La factura fue emitida {invoice_gap} días después de la atención.",
            evidence={"dias_entre_atencion_factura": invoice_gap},
            category="salud",
        ))

    return results
