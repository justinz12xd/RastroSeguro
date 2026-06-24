"""Ecuador public-data context loaders for Carlos dataset enrichment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CURATED_DIR = ROOT / "data" / "curated" / "ecuador"

CITY_TO_PROVINCE = {
    "Quito": "PICHINCHA",
    "Guayaquil": "GUAYAS",
    "Cuenca": "AZUAY",
    "Manta": "MANABI",
}

CITY_TO_CANTON = {
    "Quito": "Quito",
    "Guayaquil": "Guayaquil",
    "Cuenca": "Cuenca",
    "Manta": "Manta",
}

ECUADOR_EXTENSION_COLUMNS = [
    "supplier_ruc",
    "supplier_risk_signal_score",
    "supplier_risk_band",
    "lista_restrictiva_sercop",
    "provincia",
    "canton",
    "data_source_lineage",
]


@lru_cache(maxsize=1)
def load_restricted_rucs() -> frozenset[str]:
    path = CURATED_DIR / "sercop_sanciones_curated.csv"
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path, usecols=["ruc", "estado"], dtype=str)
    df = df.dropna(subset=["ruc"])
    df["ruc"] = df["ruc"].astype(str).str.strip()
    vigente = df["estado"].astype(str).str.lower().str.contains("vigente", na=False)
    return frozenset(df.loc[vigente, "ruc"].tolist())


@lru_cache(maxsize=1)
def load_supplier_features() -> pd.DataFrame:
    path = CURATED_DIR / "supplier_risk_features.csv"
    if not path.exists():
        return pd.DataFrame(columns=["supplier_ruc", "supplier_risk_signal_score", "supplier_risk_band"])
    df = pd.read_csv(path)
    df["supplier_ruc"] = df["supplier_ruc"].astype(str).str.strip()
    return df[["supplier_ruc", "risk_signal_score", "risk_band"]].rename(
        columns={
            "risk_signal_score": "supplier_risk_signal_score",
            "risk_band": "supplier_risk_band",
        }
    )


@lru_cache(maxsize=1)
def load_high_incident_provinces(top_n: int = 5) -> frozenset[str]:
    path = CURATED_DIR / "ecu911_monthly_agg.csv"
    if not path.exists():
        return frozenset({"GUAYAS", "PICHINCHA", "MANABI"})
    df = pd.read_csv(path, usecols=["provincia", "total_eventos"])
    agg = df.groupby("provincia", as_index=False)["total_eventos"].sum()
    top = agg.sort_values("total_eventos", ascending=False).head(top_n)["provincia"].astype(str).str.upper()
    return frozenset(top.tolist())


def _resolve_supplier_ruc(row: pd.Series) -> str:
    if pd.notna(row.get("supplier_ruc")) and str(row.get("supplier_ruc")).strip():
        return str(row["supplier_ruc"]).strip()
    benef = str(row.get("beneficiario", ""))
    if benef.startswith("PROV-RUC-"):
        return benef.replace("PROV-RUC-", "").strip()
    prov = str(row.get("id_proveedor", ""))
    if prov.startswith("PROV-"):
        return prov.replace("PROV-", "").strip()
    return ""


def enrich_with_ecuador_context(df: pd.DataFrame) -> pd.DataFrame:
    """Attach SERCOP/OCDS/ECU911/INEC lineage fields to claims dataframe."""
    out = df.copy()
    restricted = load_restricted_rucs()
    suppliers = load_supplier_features()
    high_provinces = load_high_incident_provinces()

    out["supplier_ruc"] = out.apply(_resolve_supplier_ruc, axis=1)
    if not suppliers.empty:
        merged = out[["supplier_ruc"]].merge(suppliers, on="supplier_ruc", how="left")
        if "supplier_risk_signal_score" not in out.columns:
            out["supplier_risk_signal_score"] = pd.NA
        out["supplier_risk_signal_score"] = (
            pd.to_numeric(out["supplier_risk_signal_score"], errors="coerce")
            .fillna(merged["supplier_risk_signal_score"])
            .fillna(0)
            .round(2)
        )
        if "supplier_risk_band" not in out.columns:
            out["supplier_risk_band"] = pd.NA
        out["supplier_risk_band"] = out["supplier_risk_band"].fillna(merged["supplier_risk_band"]).fillna("verde")
    else:
        out["supplier_risk_signal_score"] = pd.to_numeric(
            out.get("supplier_risk_signal_score", 0), errors="coerce"
        ).fillna(0).round(2)
        out["supplier_risk_band"] = out.get("supplier_risk_band", "verde").fillna("verde")

    out["lista_restrictiva_sercop"] = out["supplier_ruc"].isin(restricted)
    out["provincia"] = out["ciudad"].map(CITY_TO_PROVINCE).fillna("PICHINCHA")
    out["canton"] = out["ciudad"].map(CITY_TO_CANTON).fillna(out["ciudad"])

    if "zona_alta_siniestralidad" not in out.columns:
        out["zona_alta_siniestralidad"] = False
    out["zona_alta_siniestralidad"] = out["zona_alta_siniestralidad"].astype(bool) | out["provincia"].isin(high_provinces)

    sources = ["synthetic"]
    if not restricted:
        sources.append("sercop_pending")
    else:
        sources.append("sercop")
    if not suppliers.empty:
        sources.append("ocds")
    if (CURATED_DIR / "ecu911_monthly_agg.csv").exists():
        sources.append("ecu911")
    if (CURATED_DIR / "inec_dataset_agg.csv").exists():
        sources.append("inec")
    out["data_source_lineage"] = "+".join(sources)

    return out


def ecuador_coverage_metrics(df: pd.DataFrame) -> dict[str, float]:
    if len(df) == 0:
        return {
            "supplier_ruc_real_rate": 0.0,
            "lista_restrictiva_rate": 0.0,
            "ecu911_provincia_rate": 0.0,
            "lineage_with_sercop_rate": 0.0,
        }
    lineage = df.get("data_source_lineage", pd.Series(dtype=str)).astype(str)
    supplier_ruc = df.get("supplier_ruc", pd.Series(dtype=str)).astype(str)
    return {
        "supplier_ruc_real_rate": round(float((supplier_ruc.str.len() == 13).mean()), 4),
        "lista_restrictiva_rate": round(float(df.get("lista_restrictiva_sercop", False).astype(bool).mean()), 4),
        "ecu911_provincia_rate": round(float(df.get("provincia", pd.Series(dtype=str)).notna().mean()), 4),
        "lineage_with_sercop_rate": round(float(lineage.str.contains("sercop").mean()), 4),
    }


def ecuador_source_usage_metrics(df: pd.DataFrame) -> dict[str, float]:
    """Track practical usage rates for each Ecuador source signal."""
    if len(df) == 0:
        return {
            "sercop_usage_rate": 0.0,
            "ocds_usage_rate": 0.0,
            "ecu911_usage_rate": 0.0,
            "inec_usage_rate": 0.0,
        }
    lineage = df.get("data_source_lineage", pd.Series(dtype=str)).astype(str)
    supplier_score = pd.to_numeric(df.get("supplier_risk_signal_score", 0), errors="coerce").fillna(0)
    provincia = df.get("provincia", pd.Series(dtype=str)).astype(str)
    return {
        "sercop_usage_rate": round(
            float((df.get("lista_restrictiva_sercop", False).astype(bool) | lineage.str.contains("sercop")).mean()), 4
        ),
        "ocds_usage_rate": round(float((supplier_score > 0).mean()), 4),
        "ecu911_usage_rate": round(float((provincia.str.len() > 0).mean()), 4),
        "inec_usage_rate": round(float(lineage.str.contains("inec").mean()), 4),
    }
