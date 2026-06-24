"""Backward-compat shim. Canonical home: ``src.application.risk_queries``.

The read-side risk queries moved to the application layer. This module re-exports
them so any legacy import path (``from src.agent import tools``) keeps working.
First-party callers should import from ``src.application.risk_queries`` directly;
patch targets in tests live there too.
"""

from __future__ import annotations

from src.application.risk_queries import (  # noqa: F401
    OUTPUT_PATH,
    _load_scored,
    explain_claim,
    get_atypical_amount_claims,
    get_business_impact,
    get_city_risk_distribution,
    get_claim_dossier,
    get_demo_star_cases,
    get_fraud_rings,
    get_graph_connections,
    get_insured_claim_frequency,
    get_missing_documents,
    get_policy_start_border_cases,
    get_provider_red_concentration,
    get_provider_risk_ranking,
    get_repeated_patterns,
    get_risk_by_branch,
    get_similar_narratives,
    get_top_risky_claims,
    generate_executive_summary,
    recommend_review_order,
    simulate_portfolio_savings,
)
