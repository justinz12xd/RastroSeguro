"""Shared training utilities for Carlos models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.data.feature_engineering import CATEGORICAL_FEATURE_COLUMNS, MODEL_FEATURE_COLUMNS, build_feature_frame

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "data" / "synthetic" / "siniestros.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"


def load_training_frame(dataset_path: Path = DEFAULT_DATASET) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"No existe {dataset_path}. Ejecuta: python -m pipelines.data.generate_synthetic_data"
        )
    raw = pd.read_csv(dataset_path)
    return build_feature_frame(raw)


def build_preprocessor(feature_columns: list[str] | None = None) -> ColumnTransformer:
    cols = feature_columns or MODEL_FEATURE_COLUMNS
    numeric = [c for c in cols if c not in CATEGORICAL_FEATURE_COLUMNS]
    categorical = [c for c in cols if c in CATEGORICAL_FEATURE_COLUMNS]
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                numeric,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )


def split_xy(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42):
    if "etiqueta_fraude_simulada" not in df.columns:
        raise ValueError("Falta etiqueta_fraude_simulada para entrenamiento supervisado")
    x = df[MODEL_FEATURE_COLUMNS]
    y = df["etiqueta_fraude_simulada"].astype(int)
    return train_test_split(x, y, test_size=test_size, random_state=seed, stratify=y)


def classification_metrics(y_true, y_pred, y_proba=None) -> dict[str, float]:
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
    }
    if y_proba is not None and len(set(y_true)) > 1:
        metrics["auc"] = round(float(roc_auc_score(y_true, y_proba)), 4)
    return metrics


def save_artifact(path: Path, model: Any, metrics: dict[str, Any], extra: dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "metrics": metrics,
    }
    if extra:
        payload.update(extra)
    joblib.dump(payload, path)


def validate_artifact_contract(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not path.exists():
        return False, [f"missing artifact: {path}"]
    artifact = joblib.load(path)
    if not isinstance(artifact, dict):
        return False, ["artifact is not a dict payload"]
    for key in ("model", "feature_columns", "metrics"):
        if key not in artifact:
            errors.append(f"missing key {key}")
    if artifact.get("feature_columns") != MODEL_FEATURE_COLUMNS:
        errors.append("feature_columns are not aligned with MODEL_FEATURE_COLUMNS")
    return not errors, errors


def append_metrics_report(report_path: Path, section: str, metrics: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        data = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        data = {}
    data[section] = metrics
    report_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
