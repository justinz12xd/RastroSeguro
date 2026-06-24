"""Safe loading and unpacking of model artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_ARTIFACT_CACHE: dict[Path, tuple[float, Any]] = {}


def load_joblib_artifact(path: Path) -> Any | None:
    """Load a joblib artifact if available, with memory caching and automatic reloading on file changes.

    Returns None when the file or dependency is missing so the scoring pipeline
    can continue with neutral model scores.
    """
    if not path.exists():
        _ARTIFACT_CACHE.pop(path, None)
        return None

    try:
        mtime = path.stat().st_mtime
    except Exception:
        mtime = 0.0

    if path in _ARTIFACT_CACHE:
        cached_mtime, cached_artifact = _ARTIFACT_CACHE[path]
        if cached_mtime == mtime:
            return cached_artifact

    try:
        import joblib
    except Exception:
        return None

    try:
        artifact = joblib.load(path)
        _ARTIFACT_CACHE[path] = (mtime, artifact)
        return artifact
    except Exception:
        return None


def unpack_model_artifact(artifact: Any) -> tuple[Any, list[str] | None, dict[str, Any]]:
    """Support plain sklearn models or dict artifacts with metadata."""
    if isinstance(artifact, dict):
        model = artifact.get("model") or artifact.get("estimator")
        feature_columns = artifact.get("feature_columns") or artifact.get("features")
        metadata = {key: value for key, value in artifact.items() if key not in {"model", "estimator"}}
        return model, list(feature_columns) if feature_columns else None, metadata

    feature_names = getattr(artifact, "feature_names_in_", None)
    return artifact, list(feature_names) if feature_names is not None else None, {}
