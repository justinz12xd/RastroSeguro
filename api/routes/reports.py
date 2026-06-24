"""Executive report routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.routes._errors import run_endpoint
from src.application import risk_queries as tools
from src.infrastructure.repositories.scored_claims_repository import ScoredClaimsRepository
from src.reports.audit_report import build_audit_report, render_audit_markdown
from src.reports.generate_report import generate_report_dict, generate_report_markdown

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/report")
def report(format: str = Query(default="dict", pattern="^(dict|markdown)$"), top_limit: int = Query(default=10, ge=1, le=50)):
    if format == "markdown":
        return run_endpoint(lambda: {"format": "markdown", "content": generate_report_markdown(top_limit=top_limit)})
    return run_endpoint(lambda: generate_report_dict(top_limit=top_limit))


@router.get("/reports/star-cases")
def star_cases():
    return run_endpoint(tools.get_demo_star_cases)


@router.get("/reports/business-impact")
def business_impact(review_percent: float = Query(default=0.10, ge=0.01, le=1.0)):
    return run_endpoint(lambda: tools.get_business_impact(review_percent=review_percent))


@router.get("/report/savings")
def report_savings():
    return run_endpoint(tools.simulate_portfolio_savings)


@router.get("/report/audit")
def report_audit(format: str = Query(default="dict", pattern="^(dict|markdown)$"), top_limit: int = Query(default=20, ge=1, le=100)):
    def _build():
        df = ScoredClaimsRepository().read()
        payload = build_audit_report(df.to_dict("records"), top_limit=top_limit)
        if format == "markdown":
            return {"format": "markdown", "content": render_audit_markdown(payload)}
        return payload

    return run_endpoint(_build)


@router.get("/graph/fraud-rings")
def fraud_rings(limit: int = Query(default=10, ge=1, le=50)):
    return run_endpoint(lambda: tools.get_fraud_rings(limit=limit))
