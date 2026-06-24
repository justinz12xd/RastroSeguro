"""Safe ML/anomaly model scoring integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.data.feature_engineering import enrich_base_columns
from src.model_integration.artifacts import load_joblib_artifact, unpack_model_artifact
from src.model_integration.features import as_model_input, select_feature_columns
from src.model_integration.paths import ANOMALY_PATH, CLASSIFIER_PATH
from src.model_integration.predictors import anomaly_scores, classifier_scores

NEUTRAL_MODEL_SCORE = 50.0


def _claims_with_model_features(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        import pandas as pd
    except Exception:
        return claims
    frame = enrich_base_columns(pd.DataFrame(claims))
    return frame.to_dict(orient="records")


def enrich_claims_with_model_scores(
    claims: list[dict[str, Any]],
    classifier_path: Path = CLASSIFIER_PATH,
    anomaly_path: Path = ANOMALY_PATH,
) -> list[dict[str, Any]]:
    enriched = [dict(claim) for claim in claims]
    feature_ready = _claims_with_model_features(enriched)
    _apply_classifier(feature_ready, load_joblib_artifact(classifier_path))
    _apply_anomaly(feature_ready, load_joblib_artifact(anomaly_path))
    for original, scored in zip(enriched, feature_ready):
        original["score_modelo"] = scored.get("score_modelo", NEUTRAL_MODEL_SCORE)
        original["score_anomalia"] = scored.get("score_anomalia", NEUTRAL_MODEL_SCORE)
        original["modelo_disponible"] = scored.get("modelo_disponible", False)
        original["anomalia_disponible"] = scored.get("anomalia_disponible", False)
        original["modelo_features"] = scored.get("modelo_features")
        original["anomalia_features"] = scored.get("anomalia_features")
    return enriched


def enrich_claims_with_loaded_models(
    claims: list[dict[str, Any]],
    classifier_artifact: Any | None = None,
    anomaly_artifact: Any | None = None,
) -> list[dict[str, Any]]:
    enriched = [dict(claim) for claim in claims]
    feature_ready = _claims_with_model_features(enriched)
    _apply_classifier(feature_ready, classifier_artifact)
    _apply_anomaly(feature_ready, anomaly_artifact)
    for original, scored in zip(enriched, feature_ready):
        original["score_modelo"] = scored.get("score_modelo", NEUTRAL_MODEL_SCORE)
        original["score_anomalia"] = scored.get("score_anomalia", NEUTRAL_MODEL_SCORE)
        original["modelo_disponible"] = scored.get("modelo_disponible", False)
        original["anomalia_disponible"] = scored.get("anomalia_disponible", False)
        original["modelo_features"] = scored.get("modelo_features")
        original["anomalia_features"] = scored.get("anomalia_features")
    return enriched


def _apply_classifier(claims: list[dict[str, Any]], artifact: Any | None) -> None:
    if artifact is None:
        for claim in claims:
            claim.setdefault("score_modelo", NEUTRAL_MODEL_SCORE)
            claim["modelo_disponible"] = False
        return

    model, feature_columns, _metadata = unpack_model_artifact(artifact)
    if model is None:
        _apply_classifier(claims, None)
        return

    columns = select_feature_columns(claims, feature_columns)
    scores = classifier_scores(model, as_model_input(claims, columns))
    for claim, score in zip(claims, scores):
        claim["score_modelo"] = score
        claim["modelo_disponible"] = True
        claim["modelo_features"] = columns


def _apply_anomaly(claims: list[dict[str, Any]], artifact: Any | None) -> None:
    if artifact is None:
        for claim in claims:
            claim.setdefault("score_anomalia", NEUTRAL_MODEL_SCORE)
            claim["anomalia_disponible"] = False
        return

    model, feature_columns, _metadata = unpack_model_artifact(artifact)
    if model is None:
        _apply_anomaly(claims, None)
        return

    columns = select_feature_columns(claims, feature_columns)
    scores = anomaly_scores(model, as_model_input(claims, columns))
    for claim, score in zip(claims, scores):
        claim["score_anomalia"] = score
        claim["anomalia_disponible"] = True
        claim["anomalia_features"] = columns
