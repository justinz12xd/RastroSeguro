"""Common temporal risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.models import RuleResult
from src.utils.dates import days_between

Claim = dict[str, Any]


def evaluate_temporal_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []
    results.extend(_start_boundary_rule(claim))
    results.extend(_end_boundary_rule(claim))
    results.extend(_late_report_rule(claim))
    return results


def _start_boundary_rule(claim: Claim) -> list[RuleResult]:
    days = claim.get("dias_desde_inicio_poliza")
    if days is None:
        days = days_between(claim.get("fecha_inicio_poliza"), claim.get("fecha_ocurrencia"))
    if days is None or days < 0:
        return []

    if days <= 2:
        points, severity = 12, "critica"
    elif days <= 10:
        points, severity = 8, "alta"
    elif days <= 30:
        points, severity = 4, "media"
    else:
        return []

    return [RuleResult(
        code="RB-001",
        name="Siniestro cerca del inicio de póliza",
        points=points,
        severity=severity,  # type: ignore[arg-type]
        message=f"El siniestro ocurrió {days} días después del inicio de la póliza.",
        evidence={"dias_desde_inicio_poliza": days},
        category="vigencia",
    )]


def _end_boundary_rule(claim: Claim) -> list[RuleResult]:
    days = claim.get("dias_desde_fin_poliza")
    if days is None:
        days = days_between(claim.get("fecha_ocurrencia"), claim.get("fecha_fin_poliza"))
    if days is None or days < 0:
        return []

    if days <= 2:
        points, severity = 10, "alta"
    elif days <= 10:
        points, severity = 7, "alta"
    elif days <= 30:
        points, severity = 4, "media"
    else:
        return []

    return [RuleResult(
        code="RB-002",
        name="Siniestro cerca del fin de póliza",
        points=points,
        severity=severity,  # type: ignore[arg-type]
        message=f"El siniestro ocurrió a {days} días del fin de vigencia.",
        evidence={"dias_desde_fin_poliza": days},
        category="vigencia",
    )]


def _late_report_rule(claim: Claim) -> list[RuleResult]:
    days = claim.get("dias_entre_ocurrencia_reporte")
    if days is None:
        days = days_between(claim.get("fecha_ocurrencia"), claim.get("fecha_reporte"))
    if days is None:
        return []

    if days > 7:
        points, severity = 5, "media"
    elif days >= 4:
        points, severity = 3, "baja"
    else:
        return []

    return [RuleResult(
        code="RB-003",
        name="Reporte tardío",
        points=points,
        severity=severity,  # type: ignore[arg-type]
        message=f"El siniestro fue reportado {days} días después de la ocurrencia.",
        evidence={"dias_entre_ocurrencia_reporte": days},
        category="tiempo_reporte",
    )]
