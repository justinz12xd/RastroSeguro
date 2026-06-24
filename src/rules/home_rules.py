"""Home insurance-specific risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.base_rules import _bool, _num
from src.rules.models import RuleResult

Claim = dict[str, Any]


def evaluate_home_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []
    ramo = str(claim.get("ramo", "")).strip().lower()
    if ramo not in {"hogar", "home", "vivienda"}:
        return results

    if not _bool(claim.get("inspeccion_realizada")):
        results.append(RuleResult(
            code="RH-001",
            name="Daño sin inspección realizada",
            points=5,
            severity="media",
            message="El reclamo de hogar no registra inspección realizada.",
            evidence={"inspeccion_realizada": claim.get("inspeccion_realizada")},
            category="hogar",
        ))

    if _bool(claim.get("proveedor_reparacion_recurrente")):
        results.append(RuleResult(
            code="RH-002",
            name="Proveedor de reparación recurrente",
            points=6,
            severity="alta",
            message="El proveedor de reparación aparece asociado a múltiples casos observados.",
            evidence={"proveedor_reparacion_recurrente": claim.get("proveedor_reparacion_recurrente")},
            category="hogar",
        ))

    repeated = int(_num(claim.get("danios_repetidos_periodo"), _num(claim.get("danios_repetidos"))))
    if repeated >= 2:
        results.append(RuleResult(
            code="RH-003",
            name="Daños repetidos en corto periodo",
            points=7,
            severity="alta",
            message=f"Se registran {repeated} daños repetidos en un periodo corto.",
            evidence={"danios_repetidos_periodo": repeated},
            category="hogar",
        ))

    cause = str(claim.get("causa_reportada", claim.get("tipo_danio", ""))).lower()
    if any(term in cause for term in ["incendio", "inundacion", "inundación", "robo"]) and not _bool(claim.get("evidencia_fotografica", True)):
        results.append(RuleResult(
            code="RH-004",
            name="Evento relevante sin evidencia fotográfica",
            points=5,
            severity="media",
            message="El evento reportado requiere evidencia visual, pero no se registra evidencia fotográfica.",
            evidence={"causa_reportada": cause, "evidencia_fotografica": claim.get("evidencia_fotografica")},
            category="hogar",
        ))

    return results
