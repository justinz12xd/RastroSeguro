"""Read-side risk queries over the scored portfolio.

Deterministic aggregations and lookups (top risky claims, provider/city/branch
rankings, dossiers, fraud rings, demo/business-impact wrappers) consumed by the
antifraud agent, the API routes and the UI. This is the application-layer home
of what used to be the ``src.agent.tools`` god-facade; ``src.agent.tools`` now
re-exports from here for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.explainability.explain_claim import explain_claim
from src.reports.executive_summary import build_executive_report

from src.graph.fraud_rings import detect_fraud_rings_from_records
from src.infrastructure.repositories.scored_claims_repository import ScoredClaimsRepository
from src.reports.demo_differentiators import (
    build_business_impact,
    build_claim_dossier,
    build_star_case_catalog,
)
from src.scoring.final_score import OUTPUT_PATH
from src.utils.serialization import from_json_list


_cached_df: Any = None
_cached_path: Path | None = None
_cached_mtime: float | None = None


def _load_scored(data_path: Path = OUTPUT_PATH):
    global _cached_df, _cached_path, _cached_mtime
    repo = ScoredClaimsRepository(data_path)
    if not repo.exists():
        raise FileNotFoundError(f"No se encontró {data_path}. Ejecuta python -m src.scoring.final_score")

    mtime = data_path.stat().st_mtime
    if _cached_df is not None and _cached_path == data_path and _cached_mtime == mtime:
        return _cached_df

    _cached_df = repo.read()
    _cached_path = data_path
    _cached_mtime = mtime
    return _cached_df


def get_top_risky_claims(limit: int = 10, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    columns = [
        col for col in [
            "id_siniestro", "id_poliza", "id_asegurado", "ramo", "cobertura", "ciudad",
            "id_proveedor", "beneficiario", "monto_reclamado", "monto_estimado",
            "monto_pagado", "suma_asegurada", "score_reglas", "score_modelo",
            "score_anomalia", "score_nlp", "score_grafo", "score_categorico",
            "score_final", "nivel_riesgo", "alertas_activadas", "explicacion",
            "accion_sugerida", "descripcion", "fecha_ocurrencia", "fecha_reporte",
            "dias_desde_inicio_poliza", "dias_desde_fin_poliza",
            "dias_entre_ocurrencia_reporte", "documentos_completos",
            "documentos_inconsistentes",
        ] if col in df.columns
    ]
    result = df.sort_values("score_final", ascending=False).head(limit)[columns].copy()
    result = result.where(result.notna(), None)
    return result.to_dict("records")


def get_risk_by_branch(data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    grouped = df.groupby("ramo", dropna=False).agg(
        total_siniestros=("id_siniestro", "count"),
        score_promedio=("score_final", "mean"),
        casos_rojos=("nivel_riesgo", lambda s: int((s == "Rojo").sum())),
    ).reset_index()
    grouped["score_promedio"] = grouped["score_promedio"].round(2)
    return grouped.to_dict("records")


def get_provider_risk_ranking(limit: int = 10, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    if "id_proveedor" not in df.columns:
        return []
    grouped = df.groupby("id_proveedor", dropna=False).agg(
        total_siniestros=("id_siniestro", "count"),
        score_promedio=("score_final", "mean"),
        casos_rojos=("nivel_riesgo", lambda s: int((s == "Rojo").sum())),
    ).reset_index()
    grouped["score_promedio"] = grouped["score_promedio"].round(2)
    return grouped.sort_values(["casos_rojos", "score_promedio"], ascending=False).head(limit).to_dict("records")


def get_city_risk_distribution(data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    if "ciudad" not in df.columns:
        return []
    grouped = df.groupby("ciudad", dropna=False).agg(
        total_siniestros=("id_siniestro", "count"),
        score_promedio=("score_final", "mean"),
        casos_rojos=("nivel_riesgo", lambda s: int((s == "Rojo").sum())),
    ).reset_index()
    grouped["score_promedio"] = grouped["score_promedio"].round(2)
    return grouped.sort_values(["casos_rojos", "score_promedio"], ascending=False).to_dict("records")


def get_missing_documents(data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    if "documentos_completos" not in df.columns:
        return []
    mask = df["documentos_completos"].astype(str).str.lower().isin(["false", "0", "no", "nan"])
    columns = [col for col in ["id_siniestro", "ramo", "score_final", "nivel_riesgo", "documentos_completos"] if col in df.columns]
    return df[mask].sort_values("score_final", ascending=False)[columns].to_dict("records")


def recommend_review_order(limit: int = 20, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    return get_top_risky_claims(limit=limit, data_path=data_path)


def generate_executive_summary(data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    df = _load_scored(data_path)
    return build_executive_report(df.to_dict("records"), top_limit=5)


def get_similar_narratives(id_siniestro: str, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    if "siniestros_similares" not in df.columns:
        return []
    row = df[df["id_siniestro"].astype(str) == str(id_siniestro)]
    if row.empty:
        return []
    return from_json_list(row.iloc[0].get("siniestros_similares"))


def get_graph_connections(id_siniestro: str, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    df = _load_scored(data_path)
    row = df[df["id_siniestro"].astype(str) == str(id_siniestro)]
    if row.empty:
        return {"id_siniestro": id_siniestro, "connections": [], "recurring_entities": []}
    record = row.iloc[0].to_dict()
    return {
        "id_siniestro": id_siniestro,
        "score_grafo": record.get("score_grafo", 0),
        "alerta_red": record.get("alerta_red", False),
        "connections": from_json_list(record.get("conexiones_grafo")),
        "recurring_entities": from_json_list(record.get("entidades_recurrentes")),
        "explanation": record.get("explicacion_grafo", ""),
    }


def get_insured_claim_frequency(limit: int = 10, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    grouped = df.groupby("id_asegurado", dropna=False).agg(
        total_reclamos=("id_siniestro", "count"),
        score_promedio=("score_final", "mean"),
        casos_rojos=("nivel_riesgo", lambda s: int((s.astype(str).str.lower() == "rojo").sum())),
    ).reset_index()
    grouped["score_promedio"] = grouped["score_promedio"].round(2)
    return grouped.sort_values(["total_reclamos", "casos_rojos"], ascending=False).head(limit).to_dict("records")


def get_atypical_amount_claims(limit: int = 10, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    if "suma_asegurada" not in df.columns:
        return []
    ratio = df["monto_reclamado"].astype(float) / df["suma_asegurada"].astype(float).clip(lower=1)
    mask = ratio >= 0.9
    cols = [c for c in ["id_siniestro", "ramo", "monto_reclamado", "suma_asegurada", "score_final", "nivel_riesgo"] if c in df.columns]
    out = df.loc[mask, cols].copy()
    out["ratio_monto_suma"] = ratio[mask].round(4)
    return out.sort_values("score_final", ascending=False).head(limit).to_dict("records")


def get_policy_start_border_cases(limit: int = 10, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    if "dias_desde_inicio_poliza" not in df.columns:
        return []
    mask = df["dias_desde_inicio_poliza"].astype(int) <= 30
    cols = [c for c in ["id_siniestro", "ramo", "dias_desde_inicio_poliza", "score_final", "nivel_riesgo", "fecha_ocurrencia"] if c in df.columns]
    return df.loc[mask].sort_values("score_final", ascending=False).head(limit)[cols].to_dict("records")


def get_repeated_patterns(limit: int = 10, data_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    df = _load_scored(data_path)
    patterns: list[dict[str, Any]] = []
    if "alerta_narrativa" in df.columns:
        narr = df[df["alerta_narrativa"].astype(str).str.lower().isin({"true", "1", "yes"})]
        if len(narr):
            patterns.append({"patron": "narrativas_similares", "casos": int(len(narr))})
    if "alerta_red" in df.columns:
        red = df[df["alerta_red"].astype(str).str.lower().isin({"true", "1", "yes"})]
        if len(red):
            patterns.append({"patron": "entidades_recurrentes", "casos": int(len(red))})
    if "lista_restrictiva_sercop" in df.columns:
        sercop = df[df["lista_restrictiva_sercop"].astype(bool)]
        if len(sercop):
            patterns.append({"patron": "lista_restrictiva_sercop", "casos": int(len(sercop))})
    provider = (
        df.groupby("id_proveedor")
        .size()
        .reset_index(name="casos")
        .sort_values("casos", ascending=False)
        .head(limit)
    )
    for _, row in provider.iterrows():
        if row["casos"] >= 5:
            patterns.append({"patron": "proveedor_recurrente", "id_proveedor": row["id_proveedor"], "casos": int(row["casos"])})
    return patterns[:limit]


def get_claim_dossier(id_siniestro: str, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Return a juror-friendly investigation dossier for one claim."""
    return build_claim_dossier(id_siniestro, data_path=data_path)


def get_demo_star_cases(data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Return curated live-demo cases: evident, non-obvious, ethical and recurrent patterns."""
    return build_star_case_catalog(data_path=data_path)


def get_business_impact(review_percent: float = 0.10, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Return prioritization impact metrics framed as exposure, not automatic savings."""
    return build_business_impact(data_path=data_path, review_percent=review_percent)


def get_provider_red_concentration(threshold: float = 0.8, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Providers that cumulatively account for >= threshold of red alerts (jury demo)."""
    df = _load_scored(data_path)
    if "id_proveedor" not in df.columns or "nivel_riesgo" not in df.columns:
        return {"threshold": threshold, "total_casos_rojos": 0, "proveedores": []}

    red = df[df["nivel_riesgo"].astype(str).str.lower() == "rojo"]
    total_red = int(len(red))
    if total_red == 0:
        return {"threshold": threshold, "total_casos_rojos": 0, "proveedores": []}

    grouped = (
        red.groupby("id_proveedor", dropna=False)
        .size()
        .reset_index(name="casos_rojos")
        .sort_values("casos_rojos", ascending=False)
    )
    grouped["pct_del_total_rojo"] = (grouped["casos_rojos"] / total_red * 100).round(2)
    grouped["pct_acumulado"] = grouped["pct_del_total_rojo"].cumsum().round(2)

    selected = []
    for _, row in grouped.iterrows():
        selected.append({
            "id_proveedor": row["id_proveedor"],
            "casos_rojos": int(row["casos_rojos"]),
            "pct_del_total_rojo": float(row["pct_del_total_rojo"]),
            "pct_acumulado": float(row["pct_acumulado"]),
        })
        if row["pct_acumulado"] >= threshold * 100:
            break

    return {
        "threshold": threshold,
        "total_casos_rojos": total_red,
        "proveedores": selected,
        "cubre_pct_rojos": selected[-1]["pct_acumulado"] if selected else 0.0,
    }


def simulate_portfolio_savings(data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    df = _load_scored(data_path)
    from src.reports.savings_simulation import simulate_savings

    return simulate_savings(df.to_dict("records"))


def get_fraud_rings(limit: int = 10, data_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Return connected fraud rings detected across the scored portfolio."""
    df = _load_scored(data_path)
    records = df.where(df.notna(), None).to_dict("records")
    return detect_fraud_rings_from_records(records, limit=limit)
