"""Feature preparation for model artifacts."""

from __future__ import annotations

from typing import Any

DEFAULT_NUMERIC_FEATURES = [
    "dias_desde_inicio_poliza",
    "dias_desde_fin_poliza",
    "dias_entre_ocurrencia_reporte",
    "monto_reclamado",
    "monto_estimado",
    "suma_asegurada",
    "ratio_monto_suma_asegurada",
    "historial_siniestros_asegurado",
    "historial_siniestros_vehiculo",
    "score_reglas",
    "score_nlp",
    "score_grafo",
    "score_categorico",
]

DEFAULT_CATEGORICAL_FEATURES = ["ramo", "cobertura", "ciudad", "id_proveedor"]


def select_feature_columns(records: list[dict[str, Any]], configured: list[str] | None = None) -> list[str]:
    if configured:
        return configured
    available = set().union(*(record.keys() for record in records)) if records else set()
    defaults = DEFAULT_NUMERIC_FEATURES + DEFAULT_CATEGORICAL_FEATURES
    return [column for column in defaults if column in available]


def align_records(records: list[dict[str, Any]], feature_columns: list[str]) -> list[dict[str, Any]]:
    return [{column: record.get(column, 0) for column in feature_columns} for record in records]


def as_model_input(records: list[dict[str, Any]], feature_columns: list[str]):
    aligned = align_records(records, feature_columns)
    try:
        import pandas as pd
    except Exception:
        return aligned
    return pd.DataFrame(aligned, columns=feature_columns)
