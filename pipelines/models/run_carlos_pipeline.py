"""End-to-end Carlos deliverables pipeline."""

from __future__ import annotations

import argparse
import json

from pipelines.data.export_features import DEFAULT_OUTPUT as FEATURES_PATH
from pipelines.data.generate_synthetic_data import DEFAULT_OUTPUT as SINIESTROS_PATH
from pipelines.models.pipeline_steps import (
    step_build_agent_ready,
    step_build_reports,
    step_ensure_ecuador_curated,
    step_export_complementary_tables,
    step_export_features,
    step_generate_dataset,
    step_run_scoring,
    step_train_models,
)
from pipelines.models.build_star_cases import OUTPUT_PATH as STAR_CASES_PATH
from pipelines.models.build_pdf_benchmark import OUTPUT_PATH as BENCHMARK_PATH


def run_all(rows: int = 25000, seed: int = 42, scoring_rows: int = 3000) -> dict:
    step_ensure_ecuador_curated()
    step_build_agent_ready(rows=rows, seed=seed)

    df, qa_dataset = step_generate_dataset(rows=rows, seed=seed)
    complementary_paths = step_export_complementary_tables()
    features_path = step_export_features()
    classifier_path, anomaly_path = step_train_models()
    scored_path = step_run_scoring(scoring_rows)
    step_build_reports(scored_path)

    return {
        "dataset": str(SINIESTROS_PATH),
        "features": str(features_path),
        "features_meta": str(FEATURES_PATH.parent / "features_meta.json"),
        "classifier": str(classifier_path),
        "anomaly": str(anomaly_path),
        "scored": str(scored_path),
        "star_cases": str(STAR_CASES_PATH),
        "benchmark": str(BENCHMARK_PATH),
        "dataset_qa": qa_dataset,
        "scoring_rows": scoring_rows,
        "ecuador_lineage": df["data_source_lineage"].iloc[0] if "data_source_lineage" in df.columns and len(df) else "",
        "complementary_tables": complementary_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline completo de entregables Carlos")
    parser.add_argument("--rows", type=int, default=25000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scoring-rows", type=int, default=3000)
    args = parser.parse_args()
    summary = run_all(rows=args.rows, seed=args.seed, scoring_rows=args.scoring_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
