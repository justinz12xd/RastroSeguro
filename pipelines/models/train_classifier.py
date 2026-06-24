"""Train RandomForestClassifier for fraud risk signal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from pipelines.models._training_common import (
    DEFAULT_DATASET,
    MODELS_DIR,
    REPORTS_DIR,
    append_metrics_report,
    build_preprocessor,
    classification_metrics,
    load_training_frame,
    save_artifact,
    split_xy,
    validate_artifact_contract,
)

CLASSIFIER_PATH = MODELS_DIR / "fraud_classifier.joblib"
METRICS_PATH = REPORTS_DIR / "model_metrics.json"


def train_classifier(dataset_path: Path = DEFAULT_DATASET, seed: int = 42) -> Path:
    df = load_training_frame(dataset_path)
    x_train, x_test, y_train, y_test = split_xy(df, seed=seed)

    model = Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=120,
                    max_depth=12,
                    class_weight="balanced",
                    random_state=seed,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    y_proba = model.predict_proba(x_test)[:, 1]
    metrics = classification_metrics(y_test, y_pred, y_proba)
    metrics["train_rows"] = len(x_train)
    metrics["test_rows"] = len(x_test)
    metrics["positive_rate"] = round(float(df["etiqueta_fraude_simulada"].mean()), 4)
    metrics["stability"] = _estimate_stability(df, seeds=[seed, seed + 9, seed + 19])

    save_artifact(CLASSIFIER_PATH, model, metrics, extra={"model_type": "RandomForestClassifier"})
    ok, errors = validate_artifact_contract(CLASSIFIER_PATH)
    if not ok:
        raise RuntimeError(f"Artifact contract inválido: {errors}")
    append_metrics_report(METRICS_PATH, "fraud_classifier", metrics)
    return CLASSIFIER_PATH


def _estimate_stability(df, seeds: list[int]) -> dict:
    f1_values: list[float] = []
    auc_values: list[float] = []
    for local_seed in seeds:
        x_train, x_test, y_train, y_test = split_xy(df, seed=local_seed)
        probe = Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=80,
                        max_depth=10,
                        class_weight="balanced",
                        random_state=local_seed,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        probe.fit(x_train, y_train)
        local = classification_metrics(y_test, probe.predict(x_test), probe.predict_proba(x_test)[:, 1])
        f1_values.append(float(local["f1"]))
        auc_values.append(float(local.get("auc", 0.0)))
    return {
        "seeds": seeds,
        "f1_mean": round(sum(f1_values) / len(f1_values), 4),
        "f1_min": round(min(f1_values), 4),
        "f1_max": round(max(f1_values), 4),
        "auc_mean": round(sum(auc_values) / len(auc_values), 4),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Entrena models/fraud_classifier.joblib")
    p.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    path = train_classifier(args.dataset, seed=args.seed)
    print(json.dumps({"artifact": str(path), "status": "ok"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
