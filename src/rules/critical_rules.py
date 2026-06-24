"""PDF critical business rules RF-01 to RF-07."""

from __future__ import annotations

from typing import Any

from src.rules.common.coercion import as_bool, as_number
from src.rules.models import RuleResult

Claim = dict[str, Any]

FRENTE = "de frente"
DETRAS = "por detrás"

_IMPACT_KEYWORDS = {
    "frontal": ["frontal", FRENTE, "encounter"],
    "posterior": ["posterior", DETRAS, "alcance"],
    "lateral": ["lateral", "costado", "interseccion", "intersección"],
}
_IMPACT_CONTRADICTIONS = {
    "frontal": ["posterior", DETRAS, "choque por alcance"],
    "posterior": ["frontal", FRENTE, "impacto frontal"],
    "lateral": ["frontal", "posterior", FRENTE, DETRAS],
}


def evaluate_critical_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []
    results.extend(_rf01_robo_pt(claim))
    results.extend(_rf02_falsificacion_documental(claim))
    results.extend(_rf03_lista_restrictiva(claim))
    results.extend(_rf04_dinamica_imposible(claim))
    results.extend(_rf05_borde_48h(claim))
    results.extend(_rf06_demora_robo(claim))
    results.extend(_rf07_narrativa_clonada(claim))
    return results


def _rf01_robo_pt(claim: Claim) -> list[RuleResult]:
    cobertura = str(claim.get("cobertura", claim.get("tipo_evento", ""))).lower()
    if "robo" not in cobertura:
        return []
    ratio = as_number(
        claim.get("ratio_monto_suma_asegurada"),
        as_number(claim.get("monto_reclamado")) / max(as_number(claim.get("suma_asegurada")), 1),
    )
    if ratio >= 0.85:
        return [RuleResult(
            code="RF-01",
            name="Cobertura pérdida total por robo",
            points=12,
            severity="critica",
            message="Robo con monto reclamado cercano a la suma asegurada (posible pérdida total).",
            evidence={"cobertura": cobertura, "ratio_monto_suma": round(ratio, 4)},
            category="critica_pdf",
            pdf_ref="RF-01",
        )]
    return []


def _rf02_falsificacion_documental(claim: Claim) -> list[RuleResult]:
    if not as_bool(claim.get("documentos_inconsistentes")):
        return []
    return [RuleResult(
        code="RF-02",
        name="Evidencia de falsificación o adulteración documental",
        points=10,
        severity="critica",
        message="Se registran inconsistencias documentales que sugieren posible falsificación.",
        evidence={"documentos_inconsistentes": True},
        category="critica_pdf",
        pdf_ref="RF-02",
    )]


def _rf03_lista_restrictiva(claim: Claim) -> list[RuleResult]:
    if as_bool(claim.get("lista_restrictiva_sercop")):
        return [RuleResult(
            code="RF-03",
            name="Coincidencia con lista restrictiva SERCOP",
            points=10,
            severity="critica",
            message="El proveedor o beneficiario coincide con la lista restrictiva SERCOP.",
            evidence={
                "supplier_ruc": claim.get("supplier_ruc"),
                "lista_restrictiva_sercop": True,
            },
            category="critica_pdf",
            pdf_ref="RF-03",
        )]
    return []


def _rf04_dinamica_imposible(claim: Claim) -> list[RuleResult]:
    impacto = str(claim.get("tipo_impacto", "")).lower()
    descripcion = str(claim.get("descripcion", "")).lower()
    tipo_evento = str(claim.get("tipo_evento", claim.get("cobertura", ""))).lower()
    if not impacto or impacto not in _IMPACT_KEYWORDS:
        return []

    if as_bool(claim.get("dinamica_inconsistente")) or as_bool(claim.get("impacto_inconsistente")):
        return _rf04_result(claim, impacto, "flag_inconsistencia")

    if tipo_evento and all(token not in tipo_evento for token in ("choque", "accidente", "colision", "colisión")):
        return []

    # Do not penalize generic demo narratives. RF-04 should only fire when a
    # claim has an explicit inconsistency flag or the description contradicts
    # the declared impact direction.
    declared = set(_IMPACT_KEYWORDS[impacto])
    other_keywords = set(_IMPACT_CONTRADICTIONS.get(impacto, []))
    has_declared_evidence = any(keyword in descripcion for keyword in declared)
    has_contradictory_evidence = any(keyword in descripcion for keyword in other_keywords)
    if has_contradictory_evidence and not has_declared_evidence:
        return _rf04_result(claim, impacto, "contradiccion_textual")
    return []


def _rf04_result(claim: Claim, impacto: str, reason: str) -> list[RuleResult]:
    return [RuleResult(
        code="RF-04",
        name="Dinámica del accidente físicamente improbable",
        points=10,
        severity="critica",
        message="El relato no es coherente con el tipo de impacto declarado.",
        evidence={"tipo_impacto": impacto, "motivo": reason, "descripcion": claim.get("descripcion", "")[:120]},
        category="critica_pdf",
        pdf_ref="RF-04",
    )]


def _rf05_borde_48h(claim: Claim) -> list[RuleResult]:
    days = claim.get("dias_desde_inicio_poliza")
    try:
        days_int = int(days) if days is not None else None
    except (TypeError, ValueError):
        days_int = None
    if days_int is None or days_int > 2:
        return []
    return [RuleResult(
        code="RF-05",
        name="Siniestro extremo al borde de vigencia (<48h)",
        points=8,
        severity="alta",
        message=f"El siniestro ocurrió {days_int} días después del inicio de póliza.",
        evidence={"dias_desde_inicio_poliza": days_int},
        category="critica_pdf",
        pdf_ref="RF-05",
    )]


def _rf06_demora_robo(claim: Claim) -> list[RuleResult]:
    cobertura = str(claim.get("cobertura", claim.get("tipo_evento", ""))).lower()
    if "robo" not in cobertura:
        return []
    days = claim.get("dias_entre_ocurrencia_reporte")
    try:
        days_int = int(days) if days is not None else 0
    except (TypeError, ValueError):
        days_int = 0
    if days_int <= 4:
        return []
    return [RuleResult(
        code="RF-06",
        name="Demora atípica en denuncia de robo (>4 días)",
        points=8,
        severity="alta",
        message=f"Denuncia de robo reportada {days_int} días después del evento.",
        evidence={"dias_entre_ocurrencia_reporte": days_int, "cobertura": cobertura},
        category="critica_pdf",
        pdf_ref="RF-06",
    )]


def _rf07_narrativa_clonada(claim: Claim) -> list[RuleResult]:
    desc = str(claim.get("descripcion", "")).lower()
    clone_markers = ["narrativa similar", "patrón repetido", "clonada", "recurrente con narrativa"]
    has_clone_marker = any(marker in desc for marker in clone_markers)
    if (
        as_bool(claim.get("alerta_narrativa"))
        and str(claim.get("nivel_alerta_nlp", "")).lower() in {"alta", "high"}
        and has_clone_marker
    ):
        return [RuleResult(
            code="RF-07",
            name="Narrativa idéntica o clonada",
            points=8,
            severity="alta",
            message="Se detectó narrativa similar a otros reclamos del portafolio.",
            evidence={
                "alerta_narrativa": claim.get("alerta_narrativa"),
                "explicacion_nlp": claim.get("explicacion_nlp", ""),
            },
            category="critica_pdf",
            pdf_ref="RF-07",
        )]
    if has_clone_marker:
        return [RuleResult(
            code="RF-07",
            name="Narrativa idéntica o clonada",
            points=8,
            severity="alta",
            message="La descripción sugiere un patrón narrativo repetido.",
            evidence={"descripcion": claim.get("descripcion", "")[:120]},
            category="critica_pdf",
            pdf_ref="RF-07",
        )]
    return []
