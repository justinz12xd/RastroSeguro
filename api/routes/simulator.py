"""Simulation routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from api.routes._errors import run_endpoint
from src.simulator.simulate_claim import simulate_new_claim

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.post("/claim")
def simulate_claim(claim_data: dict[str, Any] = Body(...)):
    return run_endpoint(lambda: simulate_new_claim(claim_data))
