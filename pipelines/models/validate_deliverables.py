"""Validate Carlos deliverables contract and artifact integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pipelines.data.ecuador_context import ECUADOR_EXTENSION_COLUMNS
from pipelines.data.generate_synthetic_data import PDF_EXTENSION_COLUMNS
from pipelines.data.qa_metrics import ECUADOR_SOURCE_FLOORS, SIGNAL_COVERAGE_FLOOR
from pipelines.models.deliverable_checks import (
    check_artifact_contract,
    check_benchmark_questions,
    check_complementary_tables,
    check_dataset_schema,
    check_documentation,
    check_notebooks,
    check_pdf_compliance_files,
    check_qa_report,
    check_scored_artifacts,
    check_star_cases,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "data" / "synthetic" / "siniestros.csv"
FEATURES_PATH = ROOT / "data" / "processed" / "features.csv"
CLASSIFIER_PATH = ROOT / "models" / "fraud_classifier.joblib"
ANOMALY_PATH = ROOT / "models" / "anomaly_detector.joblib"
METRICS_PATH = ROOT / "reports" / "model_metrics.json"
STAR_CASES_PATH = ROOT / "reports" / "casos_estrella.json"
BENCHMARK_PATH = ROOT / "reports" / "benchmark_preguntas_pdf.json"
SCORED_PATH = ROOT / "data" / "processed" / "siniestros_scored.csv"
QA_PATH = ROOT / "data" / "synthetic" / "siniestros_qa.json"
SYNTHETIC_DIR = ROOT / "data" / "synthetic"
DOCS_DIR = ROOT / "docs"
NOTEBOOKS_DIR = ROOT / "notebooks"

PDF_DATASET_COLUMNS = PDF_EXTENSION_COLUMNS
COMPLEMENTARY_TABLES = ["polizas.csv", "asegurados.csv", "proveedores.csv", "documentos.csv", "dataset_manifest.json"]
REQUIRED_DOCS = [
    "reglas_negocio.md",
    "modelo_datos.md",
    "limitaciones.md",
    "arquitectura.md",
    "uso_ia.md",
]
PRESENTATION_PITCH = ROOT / "presentation" / "pitch.md"
R_VALIDATION_SCRIPT = ROOT / "r" / "01_validacion_metricas.R"
ORACLE_SCHEMA = ROOT / "db" / "oracle" / "schema.sql"
REQUIRED_NOTEBOOKS = [
    "01_exploracion_datos.ipynb",
    "02_modelo_fraude.ipynb",
    "03_evaluacion_modelo.ipynb",
]

REQUIRED_DATASET_COLUMNS = [
    "id_siniestro",
    "id_poliza",
    "id_asegurado",
    "ramo",
    "cobertura",
    "ciudad",
    "id_proveedor",
    "beneficiario",
    "fecha_inicio_poliza",
    "fecha_fin_poliza",
    "fecha_ocurrencia",
    "fecha_reporte",
    "monto_reclamado",
    "monto_estimado",
    "suma_asegurada",
    "descripcion",
    "documentos_completos",
    "documentos_inconsistentes",
    "historial_siniestros_asegurado",
    "etiqueta_fraude_simulada",
]


def validate() -> dict:
    errors: list[str] = []
    summary: dict[str, object] = {}

    if not DATASET_PATH.exists():
        errors.append("missing dataset")
        return {"ok": False, "errors": errors}

    df = pd.read_csv(DATASET_PATH)
    summary["dataset_rows"] = int(len(df))
    errors.extend(check_dataset_schema(df, REQUIRED_DATASET_COLUMNS, ECUADOR_EXTENSION_COLUMNS, PDF_DATASET_COLUMNS))
    summary["ecuador_extension_columns_present"] = [c for c in ECUADOR_EXTENSION_COLUMNS if c in df.columns]
    summary["pdf_extension_columns_present"] = [c for c in PDF_DATASET_COLUMNS if c in df.columns]

    comp_errors, comp_summary = check_complementary_tables(SYNTHETIC_DIR, COMPLEMENTARY_TABLES)
    errors.extend(comp_errors)
    summary.update(comp_summary)

    errors.extend(check_documentation(DOCS_DIR, REQUIRED_DOCS))
    errors.extend(check_notebooks(NOTEBOOKS_DIR, REQUIRED_NOTEBOOKS))
    errors.extend(check_pdf_compliance_files(PRESENTATION_PITCH, R_VALIDATION_SCRIPT, ORACLE_SCHEMA))

    if df["id_siniestro"].duplicated().any():
        errors.append("duplicate id_siniestro")
    if df["id_siniestro"].isna().any():
        errors.append("null id_siniestro")

    if not FEATURES_PATH.exists():
        errors.append("missing features.csv")
    else:
        summary["features_rows"] = int(len(pd.read_csv(FEATURES_PATH, usecols=["id_siniestro"])))

    clf_ok, clf_errors = check_artifact_contract(CLASSIFIER_PATH)
    an_ok, an_errors = check_artifact_contract(ANOMALY_PATH)
    if not clf_ok:
        errors.extend(clf_errors)
    if not an_ok:
        errors.extend(an_errors)

    errors.extend(check_scored_artifacts(METRICS_PATH, SCORED_PATH, STAR_CASES_PATH))

    if QA_PATH.exists():
        qa = json.loads(QA_PATH.read_text(encoding="utf-8"))
        qa_errors, qa_summary = check_qa_report(qa, SIGNAL_COVERAGE_FLOOR, ECUADOR_SOURCE_FLOORS)
        errors.extend(qa_errors)
        summary.update(qa_summary)
    else:
        errors.append(f"missing {QA_PATH}")

    if STAR_CASES_PATH.exists():
        payload = json.loads(STAR_CASES_PATH.read_text(encoding="utf-8"))
        star_errors, star_summary = check_star_cases(payload)
        errors.extend(star_errors)
        summary.update(star_summary)

    if BENCHMARK_PATH.exists():
        bench = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
        bench_errors, bench_summary = check_benchmark_questions(bench, min_questions=12)
        errors.extend(bench_errors)
        summary.update(bench_summary)
    else:
        errors.append(f"missing {BENCHMARK_PATH}")

    summary["ok"] = not errors
    summary["errors"] = errors
    return summary


def main() -> None:
    report = validate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
