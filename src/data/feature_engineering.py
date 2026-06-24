"""Feature engineering shared by training and export."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.data.portfolio_stats import PortfolioStats

NUMERIC_FEATURE_COLUMNS = [
    "dias_desde_inicio_poliza",
    "dias_desde_fin_poliza",
    "dias_entre_ocurrencia_reporte",
    "monto_reclamado",
    "monto_estimado",
    "suma_asegurada",
    "ratio_monto_suma_asegurada",
    "ratio_monto_estimado",
    "historial_siniestros_asegurado",
    "historial_siniestros_vehiculo",
    "documentos_completos_flag",
    "documentos_inconsistentes_flag",
    "tercero_identificado_flag",
    "reporte_policial_flag",
    "hay_testigos_flag",
    "ocurrio_noche_flag",
    "ocurrio_fin_semana_flag",
    "zona_alta_siniestralidad_flag",
    "conductor_recurrente_flag",
    "poliza_cercana_inicio_flag",
    "poliza_cercana_fin_flag",
    "reporte_tardio_flag",
    "monto_atipico_flag",
    "historial_alto_asegurado_flag",
    "historial_alto_vehiculo_flag",
    "proveedor_recurrencia_count",
    "beneficiario_recurrencia_count",
    "monto_gap",
    "supplier_risk_signal_score",
    "lista_restrictiva_sercop_flag",
    "supplier_risk_band_score",
]

CATEGORICAL_FEATURE_COLUMNS = [
    "ramo",
    "cobertura",
    "ciudad",
    "id_proveedor",
    "tipo_evento",
    "tipo_impacto",
    "provincia",
]

MODEL_FEATURE_COLUMNS = NUMERIC_FEATURE_COLUMNS + CATEGORICAL_FEATURE_COLUMNS


def _bool_flag(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "si", "sí", "yes", "y"}:
        return 1
    if text in {"0", "false", "no", "n"}:
        return 0
    return 0


def enrich_base_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Derive contract-friendly columns used by rules and models."""
    out = df.copy()
    if "ciudad" not in out.columns and "sucursal" in out.columns:
        out["ciudad"] = out["sucursal"]

    if "monto_reclamado" not in out.columns:
        out["monto_reclamado"] = 0.0
    if "monto_estimado" not in out.columns:
        out["monto_estimado"] = out["monto_reclamado"].astype(float).clip(lower=1.0)

    if "suma_asegurada" not in out.columns:
        out["suma_asegurada"] = (out["monto_estimado"].astype(float) * 1.25).clip(lower=500)

    fecha_ocurrencia = pd.to_datetime(out["fecha_ocurrencia"], errors="coerce") if "fecha_ocurrencia" in out.columns else None
    fecha_reporte = pd.to_datetime(out["fecha_reporte"], errors="coerce") if "fecha_reporte" in out.columns else None
    fecha_inicio = pd.to_datetime(out["fecha_inicio_poliza"], errors="coerce") if "fecha_inicio_poliza" in out.columns else None
    fecha_fin = pd.to_datetime(out["fecha_fin_poliza"], errors="coerce") if "fecha_fin_poliza" in out.columns else None

    if "dias_entre_ocurrencia_reporte" not in out.columns:
        if fecha_ocurrencia is not None and fecha_reporte is not None:
            out["dias_entre_ocurrencia_reporte"] = (fecha_reporte - fecha_ocurrencia).dt.days.fillna(0).astype(int)
        else:
            out["dias_entre_ocurrencia_reporte"] = 0

    if "dias_desde_inicio_poliza" not in out.columns:
        if fecha_ocurrencia is not None and fecha_inicio is not None:
            out["dias_desde_inicio_poliza"] = (fecha_ocurrencia - fecha_inicio).dt.days.fillna(0).astype(int)
        else:
            out["dias_desde_inicio_poliza"] = 0

    if "dias_desde_fin_poliza" not in out.columns:
        if fecha_ocurrencia is not None and fecha_fin is not None:
            out["dias_desde_fin_poliza"] = (fecha_fin - fecha_ocurrencia).dt.days.fillna(0).astype(int)
        else:
            out["dias_desde_fin_poliza"] = 0

    out["ratio_monto_suma_asegurada"] = (
        out["monto_reclamado"].astype(float) / out["suma_asegurada"].astype(float).clip(lower=1)
    ).round(4)
    out["ratio_monto_estimado"] = (
        out["monto_reclamado"].astype(float) / out["monto_estimado"].astype(float).clip(lower=1)
    ).round(4)
    out["monto_gap"] = (out["monto_reclamado"].astype(float) - out["monto_estimado"].astype(float)).round(2)

    if "documentos_completos" in out.columns:
        out["documentos_completos_flag"] = out["documentos_completos"].map(_bool_flag)
    else:
        out["documentos_completos_flag"] = 1

    if "documentos_inconsistentes" in out.columns:
        out["documentos_inconsistentes_flag"] = out["documentos_inconsistentes"].map(_bool_flag)
    else:
        out["documentos_inconsistentes_flag"] = 0

    for col, source in [
        ("tercero_identificado_flag", "tercero_identificado"),
        ("reporte_policial_flag", "reporte_policial"),
        ("hay_testigos_flag", "hay_testigos"),
        ("ocurrio_noche_flag", "ocurrio_noche"),
        ("ocurrio_fin_semana_flag", "ocurrio_fin_semana"),
        ("zona_alta_siniestralidad_flag", "zona_alta_siniestralidad"),
        ("conductor_recurrente_flag", "conductor_recurrente"),
    ]:
        if source in out.columns:
            out[col] = out[source].map(_bool_flag)
        else:
            out[col] = 0

    if "historial_siniestros_vehiculo" not in out.columns:
        out["historial_siniestros_vehiculo"] = 0
    if "historial_siniestros_asegurado" not in out.columns:
        out["historial_siniestros_asegurado"] = 0

    out["poliza_cercana_inicio_flag"] = (out["dias_desde_inicio_poliza"].astype(float) <= 30).astype(int)
    out["poliza_cercana_fin_flag"] = (out["dias_desde_fin_poliza"].astype(float) <= 30).astype(int)
    out["reporte_tardio_flag"] = (out["dias_entre_ocurrencia_reporte"].astype(float) > 7).astype(int)
    out["monto_atipico_flag"] = (out["ratio_monto_suma_asegurada"].astype(float) >= 0.9).astype(int)
    out["historial_alto_asegurado_flag"] = (out["historial_siniestros_asegurado"].astype(float) >= 3).astype(int)
    out["historial_alto_vehiculo_flag"] = (out["historial_siniestros_vehiculo"].astype(float) >= 3).astype(int)

    stats = PortfolioStats.from_frame(out)
    out = stats.enrich_frame(out)

    if "supplier_risk_signal_score" in out.columns:
        out["supplier_risk_signal_score"] = pd.to_numeric(out["supplier_risk_signal_score"], errors="coerce").fillna(0.0)
    else:
        out["supplier_risk_signal_score"] = 0.0

    if "lista_restrictiva_sercop" in out.columns:
        out["lista_restrictiva_sercop_flag"] = out["lista_restrictiva_sercop"].map(_bool_flag)
    else:
        out["lista_restrictiva_sercop_flag"] = 0

    band_map = {"verde": 0, "amarillo": 1, "rojo": 2}
    if "supplier_risk_band" in out.columns:
        out["supplier_risk_band_score"] = (
            out["supplier_risk_band"].astype(str).str.lower().map(band_map).fillna(0).astype(int)
        )
    else:
        out["supplier_risk_band_score"] = 0

    if "provincia" not in out.columns:
        out["provincia"] = "desconocido"

    for col in CATEGORICAL_FEATURE_COLUMNS:
        if col not in out.columns:
            out[col] = "desconocido"
        out[col] = out[col].astype(str).fillna("desconocido")

    return out


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    enriched = enrich_base_columns(df)
    keep_id = ["id_siniestro"] if "id_siniestro" in enriched.columns else []
    label = ["etiqueta_fraude_simulada"] if "etiqueta_fraude_simulada" in enriched.columns else []
    cols = keep_id + MODEL_FEATURE_COLUMNS + label
    return enriched[cols].copy()
