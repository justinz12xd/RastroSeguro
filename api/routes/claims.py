"""Claim and risk exploration routes for the Next.js frontend."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query
from fastapi import File, UploadFile

from api.schemas import ConfirmExtractedDocumentRequest
from api.routes._errors import run_endpoint
from src.application import risk_queries as tools
from src.application.claims.rescore_portfolio import rescore_with_population
from src.documents.claim_extraction import extract_document_review, normalize_claim_payload
from src.explainability.explain_claim import explain_claim

router = APIRouter(prefix="/api", tags=["claims"])


def _rescore_with_population(new_claims: list[dict]) -> tuple[Path, int, int]:
    """Thin adapter over the application use case (kept for route-local patching)."""
    return rescore_with_population(new_claims)


@router.get("/claims")
def list_claims(limit: int = Query(default=50, ge=1, le=200)):
    return run_endpoint(lambda: tools.get_top_risky_claims(limit=limit))


@router.get("/claims/{id_siniestro}/explanation")
def claim_explanation(id_siniestro: str):
    return run_endpoint(lambda: explain_claim(id_siniestro))


@router.get("/claims/{id_siniestro}/dossier")
def claim_dossier(id_siniestro: str):
    return run_endpoint(lambda: tools.get_claim_dossier(id_siniestro))


@router.get("/rankings/providers")
def provider_ranking(limit: int = Query(default=10, ge=1, le=100)):
    return run_endpoint(lambda: tools.get_provider_risk_ranking(limit=limit))


@router.get("/risk/cities")
def city_risk_distribution():
    return run_endpoint(tools.get_city_risk_distribution)


@router.get("/risk/branches")
def branch_risk_distribution():
    return run_endpoint(tools.get_risk_by_branch)


@router.post("/claims/upload-csv")
async def upload_claims_csv(file: UploadFile = File(...)):
    def _process() -> dict:
        filename = (file.filename or "").lower()
        if not filename.endswith(".csv"):
            raise ValueError("El archivo debe ser CSV.")

        payload = file.file.read()
        if not payload:
            raise ValueError("El CSV está vacío.")

        import io
        import pandas as pd

        uploaded = pd.read_csv(io.BytesIO(payload))
        new_claims = [row.dropna().to_dict() for _, row in uploaded.iterrows()]
        output_path, total_rows, added = _rescore_with_population(new_claims)

        return {
            "uploaded": True,
            "filename": file.filename,
            "rows_processed": total_rows,
            "rows_added": added,
            "scored_output_path": str(output_path),
        }

    return run_endpoint(_process)


@router.post("/claims/extract-document")
async def extract_claim_document(file: UploadFile = File(...)):
    def _process() -> dict:
        filename = file.filename or "documento"
        payload = file.file.read()
        return extract_document_review(filename, payload)

    return run_endpoint(_process)


@router.post("/claims/confirm-extracted-document")
async def confirm_extracted_document(request: ConfirmExtractedDocumentRequest):
    def _process() -> dict:
        raw_claim = request.claim or {}
        if not raw_claim.get("id_siniestro"):
            raise ValueError("El siniestro confirmado requiere id_siniestro.")
        if not raw_claim.get("ramo"):
            raise ValueError("El siniestro confirmado requiere ramo.")
        if raw_claim.get("monto_reclamado") in (None, ""):
            raise ValueError("El siniestro confirmado requiere monto_reclamado.")
        claim = normalize_claim_payload(raw_claim)

        output_path, total_rows, added = _rescore_with_population([claim])

        return {
            "uploaded": True,
            "document_id": request.document_id,
            "filename": request.filename,
            "rows_processed": total_rows,
            "rows_added": added,
            "selected_claim_id": claim.get("id_siniestro"),
            "scored_output_path": str(output_path),
        }

    return run_endpoint(_process)
