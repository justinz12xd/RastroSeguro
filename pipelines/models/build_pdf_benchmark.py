"""Build benchmark Q&A set aligned to reto PDF questions (12 total)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.application import risk_queries as tools
from src.explainability.explain_claim import explain_claim

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "siniestros_scored.csv"
OUTPUT_PATH = ROOT / "reports" / "benchmark_preguntas_pdf.json"


def build_benchmark(input_path: Path = INPUT_PATH) -> dict:
    df = pd.read_csv(input_path)
    top_id = str(df.sort_values("score_final", ascending=False).iloc[0]["id_siniestro"]) if len(df) else "SIN-000001"

    explain = {}
    try:
        explain = explain_claim(top_id)
    except Exception:
        explain = {"id_siniestro": top_id, "nivel_riesgo": "Rojo"}

    return {
        "questions": [
            {
                "question": "¿Cuáles son los 10 siniestros con mayor riesgo de posible fraude?",
                "expected_output": tools.get_top_risky_claims(limit=10, data_path=input_path),
            },
            {
                "question": "¿Por qué este siniestro fue marcado como alto riesgo?",
                "expected_output": explain,
            },
            {
                "question": "¿Qué proveedores concentran más alertas?",
                "expected_output": tools.get_provider_risk_ranking(limit=10, data_path=input_path),
            },
            {
                "question": "¿Qué ramos tienen mayor porcentaje de casos sospechosos?",
                "expected_output": _branch_suspicious_pct(df),
            },
            {
                "question": "¿Qué ciudades presentan mayor concentración de alertas?",
                "expected_output": tools.get_city_risk_distribution(data_path=input_path)[:10],
            },
            {
                "question": "¿Qué asegurados tienen mayor frecuencia de reclamos?",
                "expected_output": tools.get_insured_claim_frequency(limit=10, data_path=input_path),
            },
            {
                "question": "¿Qué documentos faltan en los casos críticos?",
                "expected_output": _critical_missing_docs(df),
            },
            {
                "question": "¿Qué casos tienen montos atípicos?",
                "expected_output": tools.get_atypical_amount_claims(limit=10, data_path=input_path),
            },
            {
                "question": "¿Qué siniestros ocurrieron cerca del inicio de la póliza?",
                "expected_output": tools.get_policy_start_border_cases(limit=10, data_path=input_path),
            },
            {
                "question": "¿Qué patrones se repiten en los reclamos sospechosos?",
                "expected_output": tools.get_repeated_patterns(limit=10, data_path=input_path),
            },
            {
                "question": "Genera un resumen ejecutivo de los casos críticos.",
                "expected_output": tools.generate_executive_summary(data_path=input_path),
            },
            {
                "question": "Recomienda qué casos debería revisar primero el analista.",
                "expected_output": tools.recommend_review_order(limit=10, data_path=input_path),
            },
            {
                "question": "¿Qué proveedores concentran el 80% de las alertas rojas?",
                "expected_output": tools.get_provider_red_concentration(threshold=0.8, data_path=input_path),
            },
        ],
        "rows_scored": int(len(df)),
    }


def _branch_suspicious_pct(df: pd.DataFrame) -> list[dict]:
    branches = df.groupby("ramo", dropna=False).agg(
        casos=("id_siniestro", "count"),
        sospechosos=("nivel_riesgo", lambda s: int((s.astype(str).str.lower() != "verde").sum())),
    ).reset_index()
    branches["pct_sospechosos"] = (branches["sospechosos"] / branches["casos"] * 100).round(2)
    return branches.sort_values("pct_sospechosos", ascending=False).to_dict(orient="records")


def _critical_missing_docs(df: pd.DataFrame) -> list[dict]:
    critical = df[df["nivel_riesgo"].astype(str).str.lower() == "rojo"] if "nivel_riesgo" in df.columns else df
    mask = critical["documentos_completos"].astype(str).str.lower().isin(["no", "false", "0"])
    cols = [c for c in ["id_siniestro", "nivel_riesgo", "descripcion", "documentos_completos"] if c in critical.columns]
    return critical.loc[mask].head(10)[cols].to_dict(orient="records")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera benchmark de preguntas del PDF en JSON")
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    payload = build_benchmark(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "questions": len(payload["questions"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
