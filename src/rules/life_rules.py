"""Life insurance-specific risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.base_rules import _bool, _num
from src.rules.models import RuleResult
from src.utils.dates import days_between

Claim = dict[str, Any]


def evaluate_life_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []
    ramo = str(claim.get("ramo", "")).strip().lower()
    if ramo not in {"vida", "life"}:
        return results

    if _bool(claim.get("beneficiario_recurrente")):
        results.append(RuleResult(
            code="RL-001",
            name="Beneficiario recurrente en reclamos",
            points=8,
            severity="alta",
            message="El beneficiario aparece asociado a múltiples reclamos observados.",
            evidence={"beneficiario_recurrente": claim.get("beneficiario_recurrente")},
            category="vida",
        ))

    recent_changes = int(_num(claim.get("cambios_recientes_poliza"), _num(claim.get("cambios_recientes_asegurado"))))
    if recent_changes > 0:
        results.append(RuleResult(
            code="RL-002",
            name="Cambios recientes antes del evento",
            points=7,
            severity="alta",
            message="La póliza o beneficiario tuvo cambios recientes antes del evento.",
            evidence={"cambios_recientes": recent_changes},
            category="vida",
        ))

    notification_gap = days_between(claim.get("fecha_evento", claim.get("fecha_ocurrencia")), claim.get("fecha_notificacion", claim.get("fecha_reporte")))
    if notification_gap is not None and notification_gap > 15:
        results.append(RuleResult(
            code="RL-003",
            name="Notificación tardía del evento",
            points=5,
            severity="media",
            message=f"El evento fue notificado {notification_gap} días después.",
            evidence={"dias_notificacion": notification_gap},
            category="vida",
        ))

    if not _bool(claim.get("documento_soporte", True)):
        results.append(RuleResult(
            code="RL-004",
            name="Documento soporte faltante",
            points=6,
            severity="alta",
            message="El reclamo no registra documento soporte requerido.",
            evidence={"documento_soporte": claim.get("documento_soporte")},
            category="vida",
        ))

    return results
