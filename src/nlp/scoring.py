"""NLP scoring entrypoints for claim narratives."""

from __future__ import annotations

from typing import Any

from src.nlp.narrative_signals import build_narrative_signal
from src.nlp.similarity_engine import TfidfSimilarityEngine


def score_narratives(claims: list[dict[str, Any]], threshold: float = 0.70, top_k: int = 3) -> dict[str, dict[str, Any]]:
    narratives = {
        str(claim.get("id_siniestro")): str(claim.get("descripcion", ""))
        for claim in claims
        if claim.get("id_siniestro") is not None
    }
    matches = TfidfSimilarityEngine().compute(narratives, threshold=threshold, top_k=top_k)
    return {claim_id: build_narrative_signal(claim_id, claim_matches) for claim_id, claim_matches in matches.items()}


def enrich_claims_with_nlp(claims: list[dict[str, Any]], threshold: float = 0.70, top_k: int = 3) -> list[dict[str, Any]]:
    signals = score_narratives(claims, threshold=threshold, top_k=top_k)
    enriched: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = str(claim.get("id_siniestro"))
        enriched_claim = dict(claim)
        if claim_id in signals:
            enriched_claim.update(signals[claim_id])
        enriched.append(enriched_claim)
    return enriched
