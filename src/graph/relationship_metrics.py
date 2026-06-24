"""Relationship recurrence metrics for claim entities."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.graph.entity_extraction import EntityRef, extract_entities

EntityCounts = dict[str, int]
EntityClaims = dict[str, set[str]]


def build_entity_counts(claims: list[dict[str, Any]]) -> tuple[EntityCounts, EntityClaims]:
    counts: Counter[str] = Counter()
    claims_by_entity: dict[str, set[str]] = defaultdict(set)

    for index, claim in enumerate(claims):
        claim_id = str(claim.get("id_siniestro", f"ROW-{index}"))
        seen_in_claim: set[str] = set()
        for entity in extract_entities(claim):
            if entity.key in seen_in_claim:
                continue
            counts[entity.key] += 1
            claims_by_entity[entity.key].add(claim_id)
            seen_in_claim.add(entity.key)

    return dict(counts), dict(claims_by_entity)


def recurring_entities(
    claim: dict[str, Any],
    counts: EntityCounts,
    claims_by_entity: EntityClaims,
    min_count: int = 2,
) -> list[dict[str, Any]]:
    recurring: list[dict[str, Any]] = []
    claim_id = str(claim.get("id_siniestro", ""))

    for entity in extract_entities(claim):
        count = counts.get(entity.key, 0)
        if count < min_count:
            continue
        related = sorted(claims_by_entity.get(entity.key, set()) - {claim_id})
        recurring.append({
            **entity.to_dict(),
            "total_siniestros": count,
            "siniestros_relacionados": related[:10],
        })

    return sorted(recurring, key=lambda item: item["total_siniestros"], reverse=True)
