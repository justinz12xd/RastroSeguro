"""Individual Carlos pipeline steps for testability and reuse."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pipelines.data.export_complementary_tables import export_complementary_tables
from pipelines.data.export_features import DEFAULT_OUTPUT as FEATURES_PATH
from pipelines.data.export_features import export_features
from pipelines.data.generate_synthetic_data import DEFAULT_OUTPUT as SINIESTROS_PATH
from pipelines.data.generate_synthetic_data import generate_dataset, validate_dataset
from pipelines.models.build_pdf_benchmark import OUTPUT_PATH as BENCHMARK_PATH
from pipelines.models.build_pdf_benchmark import build_benchmark
from pipelines.models.build_star_cases import OUTPUT_PATH as STAR_CASES_PATH
from pipelines.models.build_star_cases import build_star_cases
from pipelines.models.train_anomaly import train_anomaly
from pipelines.models.train_classifier import train_classifier
from src.scoring.final_score import run_scoring

ROOT = Path(__file__).resolve().parents[2]
CURATED_ECUADOR = ROOT / "data" / "curated" / "ecuador"
AGENT_READY_DIR = ROOT / "data" / "processed" / "agent_ready"
CANONICAL_SOURCE = AGENT_READY_DIR / "siniestros_canonico.csv"


def step_ensure_ecuador_curated() -> None:
    required = [
        CURATED_ECUADOR / "supplier_risk_features.csv",
        CURATED_ECUADOR / "sercop_sanciones_curated.csv",
        CURATED_ECUADOR / "ocds_contratos_curated.csv",
    ]
    if all(path.exists() for path in required):
        return
    from pipelines.ingestion.model_curated_dataset import DEFAULT_OUT, run as run_curation

    run_curation(
        DEFAULT_OUT,
        skip_ecu911=True,
        ecu911_max_rows=0,
        skip_inec=False,
        inec_max_rows=0,
    )


def step_build_agent_ready(rows: int, seed: int) -> None:
    from pipelines.ingestion.build_agent_ready_dataset import (
        CANONICAL_FIELDS,
        OUT_DIR_DEFAULT,
        build_agent_ready_siniestros,
        write_rag_chunks,
        _write_csv,
    )

    AGENT_READY_DIR.mkdir(parents=True, exist_ok=True)
    sin_rows, prov_rows, qa = build_agent_ready_siniestros(target_rows=rows, seed=seed)
    sin_path = OUT_DIR_DEFAULT / "siniestros_canonico.csv"
    prov_path = OUT_DIR_DEFAULT / "proveedores_contexto.csv"
    qa_path = OUT_DIR_DEFAULT / "qa_agent_ready.json"
    rag_path = OUT_DIR_DEFAULT / "rag_chunks_siniestros.jsonl"

    _write_csv(sin_path, sin_rows, CANONICAL_FIELDS)
    _write_csv(
        prov_path,
        prov_rows,
        [
            "supplier_ruc",
            "supplier_risk_signal_score",
            "supplier_risk_band",
            "sanciones_total",
            "contratos_total",
            "provincia_muestra",
        ],
    )
    qa["paths"] = {
        "siniestros_canonico": str(sin_path.relative_to(ROOT)),
        "proveedores_contexto": str(prov_path.relative_to(ROOT)),
        "rag_chunks": str(rag_path.relative_to(ROOT)),
    }
    qa["rag_chunks"] = write_rag_chunks(sin_rows, rag_path, limit=min(rows, 50000))
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")


def step_generate_dataset(rows: int, seed: int) -> tuple[pd.DataFrame, dict]:
    df = generate_dataset(rows=rows, seed=seed, source=CANONICAL_SOURCE)
    SINIESTROS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SINIESTROS_PATH, index=False)
    qa_dataset = validate_dataset(df)
    qa_path = SINIESTROS_PATH.parent / "siniestros_qa.json"
    qa_path.write_text(json.dumps(qa_dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return df, qa_dataset


def step_export_complementary_tables() -> dict[str, str]:
    return export_complementary_tables(SINIESTROS_PATH)


def step_export_features() -> Path:
    return export_features()


def step_train_models() -> tuple[Path, Path]:
    return train_classifier(), train_anomaly()


def sample_scoring_window(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    if max_rows <= 0 or len(df) <= max_rows:
        return df
    if "etiqueta_fraude_simulada" in df.columns:
        fraud_df = df[df["etiqueta_fraude_simulada"].astype(int) == 1]
        legit_df = df[df["etiqueta_fraude_simulada"].astype(int) == 0]
        fraud_rate = len(fraud_df) / len(df) if len(df) else 0.15
        fraud_n = min(len(fraud_df), max(1, int(max_rows * fraud_rate))) if len(fraud_df) else 0
        legit_n = min(len(legit_df), max_rows - fraud_n)
        parts: list[pd.DataFrame] = []
        if fraud_n > 0:
            parts.append(fraud_df.sample(n=fraud_n, random_state=42))
        if legit_n > 0:
            parts.append(legit_df.sample(n=legit_n, random_state=42))
        sampled = pd.concat(parts) if parts else df.sample(n=max_rows, random_state=42)
        if len(sampled) < max_rows:
            remaining = df.drop(sampled.index, errors="ignore")
            extra_n = min(len(remaining), max_rows - len(sampled))
            if extra_n > 0:
                sampled = pd.concat([sampled, remaining.sample(n=extra_n, random_state=42)])
        return sampled.head(max_rows)
    return df.sample(n=max_rows, random_state=42)


def step_run_scoring(scoring_rows: int) -> Path:
    if scoring_rows <= 0:
        return run_scoring()
    full_df = pd.read_csv(SINIESTROS_PATH)
    window_df = sample_scoring_window(full_df, scoring_rows)
    temp_input = SINIESTROS_PATH.parent / "siniestros_scoring_window.csv"
    temp_input.parent.mkdir(parents=True, exist_ok=True)
    window_df.to_csv(temp_input, index=False)
    scored = run_scoring(input_path=temp_input)
    try:
        temp_input.unlink(missing_ok=True)
    except OSError:
        pass
    return scored


def step_build_reports(scored_path: Path) -> tuple[dict, dict]:
    star_cases = build_star_cases(scored_path)
    STAR_CASES_PATH.write_text(json.dumps(star_cases, ensure_ascii=False, indent=2), encoding="utf-8")
    benchmark = build_benchmark(scored_path)
    BENCHMARK_PATH.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8")
    return star_cases, benchmark
