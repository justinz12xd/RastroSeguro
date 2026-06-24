"""Common document risk rules."""

from __future__ import annotations

from typing import Any

from src.rules.common.coercion import as_bool
from src.rules.models import RuleResult

Claim = dict[str, Any]


def evaluate_document_rules(claim: Claim) -> list[RuleResult]:
    results: list[RuleResult] = []

    if not as_bool(claim.get("documentos_completos")):
        results.append(RuleResult(
            code="RB-006",
            name="Documentos incompletos",
            points=4,
            severity="media",
            message="El expediente documental está incompleto.",
            evidence={"documentos_completos": claim.get("documentos_completos")},
            category="documentos",
        ))

    # RF-02 in critical_rules owns inconsistent-document signal; skip RB-007 here.

    return results
