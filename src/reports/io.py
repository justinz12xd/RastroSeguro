"""Input helpers for report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.scoring.final_score import OUTPUT_PATH


def load_scored_claims(data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró {data_path}. Ejecuta python -m src.scoring.final_score")
    import pandas as pd

    return pd.read_csv(data_path).to_dict("records")
