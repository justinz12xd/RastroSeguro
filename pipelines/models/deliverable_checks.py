"""Modular deliverable validation checks."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd


def check_dataset_schema(
    df: pd.DataFrame,
    required_columns: list[str],
    ecuador_columns: list[str],
    pdf_columns: list[str],
) -> list[str]:
    errors: list[str] = []
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        errors.append(f"missing dataset columns: {missing_cols}")
    missing_ecuador = [c for c in ecuador_columns if c not in df.columns]
    if missing_ecuador:
        errors.append(f"missing ecuador extension columns: {missing_ecuador}")
    missing_pdf = [c for c in pdf_columns if c not in df.columns]
    if missing_pdf:
        errors.append(f"missing pdf extension columns: {missing_pdf}")
    return errors


def check_complementary_tables(synthetic_dir: Path, tables: list[str]) -> tuple[list[str], dict]:
    errors: list[str] = []
    summary: dict[str, object] = {}
    for table in tables:
        path = synthetic_dir / table
        if not path.exists():
            errors.append(f"missing complementary table {path}")
        elif path.suffix == ".csv":
            header = pd.read_csv(path, nrows=0)
            rows = len(pd.read_csv(path, usecols=[header.columns[0]]))
            summary[f"rows_{table.replace('.csv', '')}"] = rows
            if rows < 1:
                errors.append(f"empty complementary table {table}")
    return errors, summary


def check_documentation(docs_dir: Path, required_docs: list[str]) -> list[str]:
    return [f"missing doc {doc}" for doc in required_docs if not (docs_dir / doc).exists()]


def check_notebooks(notebooks_dir: Path, required_notebooks: list[str]) -> list[str]:
    return [f"missing notebook {nb}" for nb in required_notebooks if not (notebooks_dir / nb).exists()]


def check_pdf_compliance_files(pitch_path: Path, r_script_path: Path, oracle_schema_path: Path) -> list[str]:
    errors: list[str] = []
    if not pitch_path.exists():
        errors.append(f"missing {pitch_path}")
    if not r_script_path.exists():
        errors.append(f"missing {r_script_path}")
    if not oracle_schema_path.exists():
        errors.append(f"missing {oracle_schema_path}")
    return errors


def check_artifact_contract(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not path.exists():
        return False, [f"missing {path}"]
    artifact = joblib.load(path)
    if not isinstance(artifact, dict):
        return False, [f"{path.name} no es dict compatible"]
    for key in ("model", "feature_columns", "metrics"):
        if key not in artifact:
            errors.append(f"{path.name} missing key {key}")
    return not errors, errors


def check_scored_artifacts(metrics_path: Path, scored_path: Path, star_cases_path: Path) -> list[str]:
    errors: list[str] = []
    if not metrics_path.exists():
        errors.append(f"missing {metrics_path}")
    if not scored_path.exists():
        errors.append(f"missing {scored_path}")
    elif "rule_trace" not in pd.read_csv(scored_path, nrows=0).columns:
        errors.append("missing rule_trace in siniestros_scored.csv")
    if not star_cases_path.exists():
        errors.append(f"missing {star_cases_path}")
    return errors


def check_qa_report(
    qa: dict,
    signal_floor: float,
    source_floors: dict[str, float],
) -> tuple[list[str], dict]:
    errors: list[str] = []
    summary: dict[str, object] = {
        "qa_ok": bool(qa.get("ok")),
        "ecuador_coverage": qa.get("ecuador_coverage", {}),
        "ecuador_source_usage": qa.get("ecuador_source_usage", {}),
    }
    coverage = qa.get("signal_coverage", {})
    weak = [k for k, v in coverage.items() if float(v) < signal_floor]
    if weak:
        errors.append(f"signal coverage too low: {weak}")
    ecuador = qa.get("ecuador_coverage", {})
    if ecuador.get("supplier_ruc_real_rate", 0) < 0.5:
        errors.append("ecuador supplier_ruc_real_rate below 0.5")
    if ecuador.get("lista_restrictiva_rate", 0) < 0.001:
        errors.append("ecuador lista_restrictiva_rate below 0.001")
    for key, floor in source_floors.items():
        if qa.get("ecuador_source_usage", {}).get(key, 0) < floor:
            errors.append(f"ecuador {key} below {floor}")
    return errors, summary


def check_star_cases(payload: dict) -> tuple[list[str], dict]:
    errors: list[str] = []
    levels = {str(item.get("nivel_riesgo", "")).lower() for item in payload.get("cases", [])}
    if "rojo" not in levels or "amarillo" not in levels:
        errors.append("casos_estrella must include both Rojo and Amarillo")
    return errors, {"star_cases_count": int(payload.get("count", 0))}


def check_benchmark_questions(bench: dict, min_questions: int = 12) -> tuple[list[str], dict]:
    errors: list[str] = []
    q_count = len(bench.get("questions", []))
    if q_count < min_questions:
        errors.append("benchmark preguntas insuficiente (<12)")
    return errors, {"benchmark_questions": q_count}
