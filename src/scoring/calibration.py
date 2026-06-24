"""Portfolio risk calibration for scored claims."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from src.utils.risk_levels import suggested_action

TARGET_RISK_DISTRIBUTION = {
    "verde": 0.60,
    "amarillo": 0.25,
    "rojo": 0.15,
}

CRITICAL_RULE_CODES = frozenset({"RF-01", "RF-02", "RF-03", "RF-04", "RF-05", "RF-06", "RF-07", "RB-007"})


def _has_critical_rule(rule_trace_raw: Any) -> bool:
    if rule_trace_raw is None or (isinstance(rule_trace_raw, float) and pd.isna(rule_trace_raw)):
        return False
    if isinstance(rule_trace_raw, str):
        try:
            trace = json.loads(rule_trace_raw)
        except json.JSONDecodeError:
            return False
    elif isinstance(rule_trace_raw, list):
        trace = rule_trace_raw
    else:
        return False
    for item in trace:
        code = str(item.get("code", ""))
        pdf_ref = str(item.get("pdf_ref", ""))
        if code in CRITICAL_RULE_CODES or pdf_ref.startswith("RF-"):
            return True
    return False


def apply_portfolio_calibration(df: pd.DataFrame) -> pd.DataFrame:
    """Calibrate portfolio mix using score_final percentiles after hybrid scoring."""
    if df.empty or "score_final" not in df.columns:
        return df

    calibrated = df.copy()
    rank_desc = calibrated["score_final"].rank(method="first", ascending=False)
    pct_desc = (rank_desc - 1) / max(len(calibrated) - 1, 1)

    red_cut = TARGET_RISK_DISTRIBUTION["rojo"]
    amber_cut = TARGET_RISK_DISTRIBUTION["rojo"] + TARGET_RISK_DISTRIBUTION["amarillo"]

    def level_from_pct(p: float) -> str:
        if p <= red_cut:
            return "Rojo"
        if p <= amber_cut:
            return "Amarillo"
        return "Verde"

    calibrated["nivel_riesgo"] = pct_desc.map(level_from_pct)

    if "rule_trace" in calibrated.columns:
        critical_mask = calibrated["rule_trace"].map(_has_critical_rule)
        calibrated.loc[critical_mask, "nivel_riesgo"] = "Rojo"
    elif "score_reglas" in calibrated.columns:
        strong = calibrated["score_reglas"].astype(float) >= 90
        medium = calibrated["score_reglas"].astype(float) >= 75
        calibrated.loc[strong, "nivel_riesgo"] = "Rojo"
        calibrated.loc[~strong & medium, "nivel_riesgo"] = calibrated.loc[~strong & medium, "nivel_riesgo"].replace(
            {"Verde": "Amarillo"}
        )

    mapped_score = calibrated["nivel_riesgo"].map({"Verde": 30.0, "Amarillo": 60.0, "Rojo": 85.0}).astype(float)
    calibrated["score_final"] = calibrated["score_final"].astype(float) * 0.35 + mapped_score * 0.65
    calibrated["score_final"] = calibrated["score_final"].clip(0, 100).round(2)
    calibrated["accion_sugerida"] = calibrated["nivel_riesgo"].map(suggested_action)
    return calibrated
