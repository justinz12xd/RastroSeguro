"""Route-level error translation helpers."""

from __future__ import annotations

from typing import Any, Callable

from fastapi.responses import JSONResponse

from api.schemas import failure, success

DEFAULT_SCORING_HINT = "Ejecuta primero el scoring para generar data/processed/siniestros_scored.csv."


def run_endpoint(handler: Callable[[], Any]) -> dict[str, Any] | JSONResponse:
    try:
        return success(handler())
    except FileNotFoundError as exc:
        return JSONResponse(status_code=404, content=failure(str(exc), hint=DEFAULT_SCORING_HINT))
    except ValueError as exc:
        return JSONResponse(status_code=404, content=failure(str(exc)))
    except Exception as exc:
        return JSONResponse(status_code=500, content=failure("Error interno del puente API.", details=str(exc)))
