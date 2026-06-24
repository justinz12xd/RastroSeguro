"""Train IsolationForest anomaly detector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from pipelines.models._training_common import (
    DEFAULT_DATASET,
    MODELS_DIR,
    REPORTS_DIR,
    append_metrics_report,
    build_preprocessor,
    load_training_frame,
    save_artifact,
    validate_artifact_contract,
)

ANOMALY_PATH = MODELS_DIR / "anomaly_detector.joblib"
METRICS_PATH = REPORTS_DIR / "model_metrics.json"


def train_anomaly(dataset_path: Path = DEFAULT_DATASET, seed: int = 42) -> Path:
    df = load_training_frame(dataset_path)
    x = df.drop(columns=["etiqueta_fraude_simulada"], errors="ignore")

    model = Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "iso",
                IsolationForest(
                    n_estimators=200,
                    contamination=min(0.45, max(0.02, float(df["etiqueta_fraude_simulada"].mean()))),
                    random_state=seed,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(x)
    preds = model.predict(x)
    anomaly_rate = round(float((preds == -1).mean()), 4)

    # Weak proxy validation: overlap between anomalies and simulated fraud label.
    if "etiqueta_fraude_simulada" in df.columns:
        y = df["etiqueta_fraude_simulada"].astype(int).to_numpy()
        overlap = float(((preds == -1) & (y == 1)).sum() / max(1, (preds == -1).sum()))
    else:
        overlap = 0.0

    metrics = {
        "anomaly_rate": anomaly_rate,
        "fraud_overlap_in_anomalies": round(overlap, 4),
        "rows": len(df),
        "stability": _estimate_stability(df, seeds=[seed, seed + 11, seed + 23]),
    }

    save_artifact(ANOMALY_PATH, model, metrics, extra={"model_type": "IsolationForest"})
    ok, errors = validate_artifact_contract(ANOMALY_PATH)
    if not ok:
        raise RuntimeError(f"Artifact contract inválido: {errors}")
    append_metrics_report(METRICS_PATH, "anomaly_detector", metrics)
    return ANOMALY_PATH


def _estimate_stability(df, seeds: list[int]) -> dict:
    x = df.drop(columns=["etiqueta_fraude_simulada"], errors="ignore")
    y = df["etiqueta_fraude_simulada"].astype(int).to_numpy()
    anomaly_rates: list[float] = []
    overlaps: list[float] = []
    for local_seed in seeds:
        probe = Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "iso",
                    IsolationForest(
                        n_estimators=120,
                        contamination=min(0.45, max(0.02, float(df["etiqueta_fraude_simulada"].mean()))),
                        random_state=local_seed,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        probe.fit(x)
        preds = probe.predict(x)
        anomaly_rates.append(float((preds == -1).mean()))
        overlap = float(((preds == -1) & (y == 1)).sum() / max(1, (preds == -1).sum()))
        overlaps.append(overlap)
    return {
        "seeds": seeds,
        "anomaly_rate_mean": round(sum(anomaly_rates) / len(anomaly_rates), 4),
        "anomaly_rate_min": round(min(anomaly_rates), 4),
        "anomaly_rate_max": round(max(anomaly_rates), 4),
        "overlap_mean": round(sum(overlaps) / len(overlaps), 4),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Entrena models/anomaly_detector.joblib")
    p.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    path = train_anomaly(args.dataset, seed=args.seed)
    print(json.dumps({"artifact": str(path), "status": "ok"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
