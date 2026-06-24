"""Dataset QA metrics and validation thresholds."""

from __future__ import annotations

import pandas as pd

from pipelines.data.claim_signals import signal_coverage
from pipelines.data.ecuador_context import ecuador_coverage_metrics, ecuador_source_usage_metrics
from src.data.portfolio_stats import PortfolioStats

SIGNAL_COVERAGE_FLOOR = 0.01

ECUADOR_COVERAGE_FLOORS = {
    "supplier_ruc_real_rate": 0.5,
    "lista_restrictiva_rate": 0.001,
    "ecu911_provincia_rate": 0.95,
    "lineage_with_sercop_rate": 0.95,
}

ECUADOR_SOURCE_FLOORS = {
    "sercop_usage_rate": 0.95,
    "ocds_usage_rate": 0.5,
    "ecu911_usage_rate": 0.95,
    "inec_usage_rate": 0.95,
}

REQUIRED_DATASET_COLUMNS = [
    "id_siniestro",
    "ramo",
    "fecha_ocurrencia",
    "monto_reclamado",
    "monto_pagado",
    "estado",
    "sucursal",
    "chasis_hash",
    "motor_hash",
    "etiqueta_fraude_simulada",
]


def validate_structural(df: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if "id_siniestro" in df.columns and df["id_siniestro"].duplicated().any():
        issues.append("id_siniestro duplicado")
    for col in REQUIRED_DATASET_COLUMNS:
        if col not in df.columns:
            issues.append(f"falta columna {col}")
        elif df[col].isna().any():
            issues.append(f"nulos en {col}")
    return issues


def build_distribution_metrics(df: pd.DataFrame) -> dict:
    by_ramo = df["ramo"].value_counts(normalize=True).round(4).to_dict()
    by_city = df["ciudad"].value_counts(normalize=True).round(4).head(10).to_dict()
    by_provincia = (
        df["provincia"].value_counts(normalize=True).round(4).head(10).to_dict()
        if "provincia" in df.columns
        else {}
    )
    return {
        "rows": len(df),
        "unique_ids": int(df["id_siniestro"].nunique()),
        "fraud_rate": round(float(df["etiqueta_fraude_simulada"].mean()), 4),
        "distribution_by_ramo": by_ramo,
        "distribution_by_city_top10": by_city,
        "distribution_by_provincia_top10": by_provincia,
    }


def validate_business_thresholds(
    coverage: dict[str, float],
    ecuador_coverage: dict[str, float],
    source_usage: dict[str, float],
) -> list[str]:
    issues: list[str] = []
    weak_signals = [name for name, ratio in coverage.items() if ratio < SIGNAL_COVERAGE_FLOOR]
    if weak_signals:
        issues.append(f"cobertura baja de señales: {weak_signals}")
    weak_ecuador = [k for k, floor in ECUADOR_COVERAGE_FLOORS.items() if ecuador_coverage.get(k, 0.0) < floor]
    if weak_ecuador:
        issues.append(f"cobertura Ecuador insuficiente: {weak_ecuador}")
    weak_sources = [k for k, floor in ECUADOR_SOURCE_FLOORS.items() if source_usage.get(k, 0.0) < floor]
    if weak_sources:
        issues.append(f"uso de fuentes Ecuador insuficiente: {weak_sources}")
    return issues


def build_dataset_qa(df: pd.DataFrame, stats: PortfolioStats | None = None) -> dict:
    """Build full QA report with structural and business validations."""
    stats = stats or PortfolioStats.from_frame(df)
    issues = validate_structural(df)
    coverage = signal_coverage(df, stats=stats)
    ecuador_coverage = ecuador_coverage_metrics(df)
    source_usage = ecuador_source_usage_metrics(df)
    issues.extend(validate_business_thresholds(coverage, ecuador_coverage, source_usage))
    qa = {
        **build_distribution_metrics(df),
        "signal_coverage": coverage,
        "ecuador_coverage": ecuador_coverage,
        "ecuador_source_usage": source_usage,
        "ok": not issues,
        "issues": issues,
    }
    return qa
