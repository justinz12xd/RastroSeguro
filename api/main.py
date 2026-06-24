"""FastAPI bridge for the RastroSeguro Next.js frontend."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import agent, claims, health, reports, simulator
from api.schemas import failure


def create_app() -> FastAPI:
    app = FastAPI(
        title="RastroSeguro API",
        description="HTTP bridge between the Next.js frontend and the Python antifraud core.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=failure(
                "La solicitud no cumple el contrato esperado.",
                hint="Revisa campos requeridos, tipos y parámetros enviados desde Next.js.",
                details=exc.errors(),
            ),
        )

    @app.get("/")
    def root_probe() -> dict:
        """Azure App Service and load balancers often probe `/` by default."""
        return {"service": "rastroseguro-api", "status": "ok"}

    @app.get("/health")
    def legacy_health_probe() -> dict:
        """Compatibility path for health checks configured without the `/api` prefix."""
        return {"service": "rastroseguro-api", "status": "ok"}

    app.include_router(health.router)
    app.include_router(claims.router)
    app.include_router(simulator.router)
    app.include_router(agent.router)
    app.include_router(reports.router)
    return app


def _allowed_origins() -> list[str]:
    configured = os.environ.get("RASTRO_API_CORS_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app = create_app()
