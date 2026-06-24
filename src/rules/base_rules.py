"""Base auditable rules that apply to all insurance branches."""

from __future__ import annotations

from typing import Any

from src.rules.common.amount_rules import evaluate_amount_rules
from src.rules.common.coercion import as_bool as _bool
from src.rules.common.coercion import as_number as _num
from src.rules.common.document_rules import evaluate_document_rules
from src.rules.common.recurrence_rules import evaluate_recurrence_rules
from src.rules.common.temporal_rules import evaluate_temporal_rules
from src.rules.models import RuleResult

Claim = dict[str, Any]

BASE_RULE_EVALUATORS = (
    evaluate_temporal_rules,
    evaluate_amount_rules,
    evaluate_document_rules,
    evaluate_recurrence_rules,
)


def evaluate_base_rules(claim: Claim) -> list[RuleResult]:
    """Evaluate common risk signals for any branch."""
    results: list[RuleResult] = []
    for evaluator in BASE_RULE_EVALUATORS:
        results.extend(evaluator(claim))
    return results
