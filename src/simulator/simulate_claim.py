"""Simulation entrypoint for evaluating a new claim without persisting it.

The simulator runs the real-time RastroSeguro pipeline against an unsaved claim
and returns both the legacy explanation fields and UI-ready sections for Justin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.categorical.scoring import enrich_claims_with_categorical
from src.explainability.explain_claim import explain_unsaved_claim
from src.graph.scoring import enrich_claims_with_graph
from src.model_integration.scoring import enrich_claims_with_model_scores
from src.nlp.scoring import enrich_claims_with_nlp
from src.scoring.final_score import OUTPUT_PATH
from src.simulator.context import load_historical_claims
from src.simulator.normalization import normalize_simulated_claim
from src.simulator.response import build_simulation_response


def simulate_new_claim(claim_data: dict[str, Any], data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Evaluate a new claim through rules, model scores, NLP, graph and categories."""
    claim = normalize_simulated_claim(claim_data)
    database_claims, context = load_historical_claims(data_path)
    _normalize_provider_against_history(claim, database_claims)

    all_claims = database_claims + [claim]
    all_claims = enrich_claims_with_graph(all_claims)
    all_claims = enrich_claims_with_categorical(all_claims)
    all_claims = enrich_claims_with_model_scores(all_claims)

    if any(item.get("descripcion") for item in all_claims):
        all_claims = enrich_claims_with_nlp(all_claims)

    simulated_enriched = all_claims[-1]
    explanation = explain_unsaved_claim(simulated_enriched)
    return build_simulation_response(explanation, simulated_enriched, claim, context)



def _normalize_provider_against_history(claim: dict[str, Any], historical_claims: list[dict[str, Any]]) -> None:
    """Map UI provider typos like PROV-0012 to a provider code present in history."""
    raw = str(claim.get("id_proveedor", "")).strip().upper()
    if not raw:
        return

    known_counts: dict[str, int] = {}
    for item in historical_claims:
        provider = str(item.get("id_proveedor", "")).strip().upper()
        if provider:
            known_counts[provider] = known_counts.get(provider, 0) + 1

    if raw in known_counts:
        claim["id_proveedor"] = raw
        return

    import re

    match = re.match(r"^([A-Z]+)-0*(\d+)$", raw)
    if not match:
        claim["id_proveedor"] = raw
        return

    prefix, number = match.groups()
    number_int = int(number)
    candidates = [
        f"{prefix}-{number_int}",
        f"{prefix}-{number_int:02d}",
        f"{prefix}-{number_int:03d}",
    ]
    present = [candidate for candidate in candidates if candidate in known_counts]
    claim["id_proveedor"] = max(present, key=lambda candidate: known_counts[candidate]) if present else candidates[-1]
