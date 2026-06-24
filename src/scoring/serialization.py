"""JSON serialization helpers for scored dataframe columns."""

from __future__ import annotations

import pandas as pd

from src.utils.serialization import to_json

JSON_SCORE_COLUMNS = (
    "alertas_activadas",
    "siniestros_similares",
    "entidades_recurrentes",
    "conexiones_grafo",
    "senales_categoricas",
    "modelo_features",
    "anomalia_features",
    "rule_trace",
)


def serialize_scored_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in JSON_SCORE_COLUMNS:
        if column in result.columns:
            result[column] = result[column].apply(to_json)
    return result
