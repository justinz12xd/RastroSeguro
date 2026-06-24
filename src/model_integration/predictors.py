"""Prediction adapters for Carlos' classifier and anomaly models."""

from __future__ import annotations

from typing import Any

from src.utils.risk_levels import clamp_score


def classifier_scores(model: Any, model_input: Any) -> list[float]:
    """Return 0-100 supervised risk scores."""
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(model_input)
        return [round(clamp_score(row[-1] * 100), 2) for row in probabilities]

    predictions = model.predict(model_input)
    return [100.0 if int(prediction) == 1 else 0.0 for prediction in predictions]


def anomaly_scores(model: Any, model_input: Any) -> list[float]:
    """Return 0-100 anomaly scores where higher means more unusual."""
    if hasattr(model, "predict"):
        predictions = model.predict(model_input)
        # IsolationForest convention: -1 anomaly, 1 normal.
        return [80.0 if int(prediction) == -1 else 20.0 for prediction in predictions]

    if hasattr(model, "score_samples"):
        raw_scores = list(model.score_samples(model_input))
        return _invert_minmax(raw_scores)

    return []


def _invert_minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if low == high:
        return [50.0 for _ in values]
    return [round(clamp_score((1 - ((value - low) / (high - low))) * 100), 2) for value in values]
