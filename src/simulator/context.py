"""Historical context loading for simulations."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

SERIALIZED_COLUMNS = {
    "alertas_activadas",
    "siniestros_similares",
    "entidades_recurrentes",
    "conexiones_grafo",
    "senales_categoricas",
    "modelo_features",
    "anomalia_features",
}


def load_historical_claims(data_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load scored historical claims without requiring pandas at runtime."""
    if not data_path.exists():
        return [], {
            "historical_claims_loaded": False,
            "historical_claims_count": 0,
            "history_path": str(data_path),
            "history_status": "missing",
        }

    try:
        with data_path.open("r", encoding="utf-8", newline="") as file:
            rows = [
                _clean_row(row)
                for row in csv.DictReader(file)
            ]
    except OSError as exc:
        return [], {
            "historical_claims_loaded": False,
            "historical_claims_count": 0,
            "history_path": str(data_path),
            "history_status": "error",
            "history_error": str(exc),
        }

    return rows, {
        "historical_claims_loaded": True,
        "historical_claims_count": len(rows),
        "history_path": str(data_path),
        "history_status": "ok",
    }


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: value for key, value in row.items() if key not in SERIALIZED_COLUMNS}
    return {key: _coerce_csv_value(value) for key, value in cleaned.items()}


def _coerce_csv_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        number = float(text)
    except ValueError:
        return value
    return int(number) if number.is_integer() else number
