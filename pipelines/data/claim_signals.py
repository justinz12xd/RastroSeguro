"""Unified PDF signal masks and coverage for synthetic dataset generation."""

from __future__ import annotations

import pandas as pd

from src.data.portfolio_stats import PortfolioStats, RECURRENCE_THRESHOLD

SIGNAL_COLUMNS = {
    "borde_vigencia": "signal_borde_vigencia",
    "reporte_tardio": "signal_reporte_tardio",
    "proveedor_recurrente": "signal_proveedor_recurrente",
    "beneficiario_recurrente": "signal_beneficiario_recurrente",
    "documentos_inconsistentes": "signal_documentos_inconsistentes",
    "monto_atipico": "signal_monto_atipico",
    "frecuencia_asegurado": "signal_frecuencia_asegurado",
    "frecuencia_vehiculo": "signal_frecuencia_vehiculo",
    "conductor_recurrente": "signal_conductor_recurrente",
    "sin_tercero": "signal_sin_tercero",
}

SIGNAL_NAMES = tuple(SIGNAL_COLUMNS.keys())


def compute_signal_masks(df: pd.DataFrame, stats: PortfolioStats | None = None) -> dict[str, pd.Series]:
    """Return boolean masks for each PDF signal using shared portfolio stats."""
    if len(df) == 0:
        return {name: pd.Series(dtype=bool) for name in SIGNAL_NAMES}

    stats = stats or PortfolioStats.from_frame(df)
    is_vehicle = df["ramo"].astype(str).str.lower() == "vehiculos"
    monto_ratio = stats.monto_ratio(df)
    provider_rec = stats.proveedor_recurrencia(df)
    beneficiary_rec = stats.beneficiario_recurrencia(df)

    return {
        "borde_vigencia": (
            (df["dias_desde_inicio_poliza"].astype(int) <= 30)
            | (df["dias_desde_fin_poliza"].astype(int) <= 30)
        ),
        "reporte_tardio": df["dias_entre_ocurrencia_reporte"].astype(int) > 7,
        "proveedor_recurrente": provider_rec >= RECURRENCE_THRESHOLD,
        "beneficiario_recurrente": beneficiary_rec >= RECURRENCE_THRESHOLD,
        "documentos_inconsistentes": df["documentos_inconsistentes"].astype(bool),
        "monto_atipico": monto_ratio >= 0.9,
        "frecuencia_asegurado": df["historial_siniestros_asegurado"].astype(int) >= 3,
        "frecuencia_vehiculo": df["historial_siniestros_vehiculo"].astype(int) >= 3,
        "conductor_recurrente": df["conductor_recurrente"].astype(bool),
        "sin_tercero": is_vehicle & (~df["tercero_identificado"].astype(bool)),
    }


def signal_coverage_from_masks(masks: dict[str, pd.Series]) -> dict[str, float]:
    if not masks:
        return dict.fromkeys(SIGNAL_NAMES, 0.0)
    return {name: round(float(masks[name].mean()), 4) for name in SIGNAL_NAMES if name in masks}


def signal_coverage(df: pd.DataFrame, stats: PortfolioStats | None = None) -> dict[str, float]:
    masks = compute_signal_masks(df, stats=stats)
    return signal_coverage_from_masks(masks)


def _fraud_label_from_masks(masks: dict[str, pd.Series]) -> pd.Series:
    weighted = (
        masks["borde_vigencia"].astype(int) * 2
        + masks["reporte_tardio"].astype(int) * 2
        + masks["proveedor_recurrente"].astype(int) * 2
        + masks["beneficiario_recurrente"].astype(int)
        + masks["documentos_inconsistentes"].astype(int) * 3
        + masks["monto_atipico"].astype(int) * 2
        + masks["frecuencia_asegurado"].astype(int) * 2
        + masks["frecuencia_vehiculo"].astype(int)
        + masks["conductor_recurrente"].astype(int)
        + masks["sin_tercero"].astype(int)
    )
    return (weighted >= 8).astype(int)


def apply_signals_to_frame(df: pd.DataFrame, stats: PortfolioStats | None = None) -> pd.DataFrame:
    """Write signal_* columns and simulated fraud label from unified masks."""
    stats = stats or PortfolioStats.from_frame(df)
    masks = compute_signal_masks(df, stats=stats)
    out = stats.enrich_frame(df)
    for name, column in SIGNAL_COLUMNS.items():
        out[column] = masks[name]
    out["etiqueta_fraude_simulada"] = _fraud_label_from_masks(masks)
    return out
