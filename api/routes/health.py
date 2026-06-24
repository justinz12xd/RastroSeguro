"""Healthcheck routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import success

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict:
    return success({"service": "rastroseguro-api", "status": "ok"})
