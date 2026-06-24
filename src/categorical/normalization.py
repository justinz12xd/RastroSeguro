"""Categorical value normalization helpers."""

from __future__ import annotations

import unicodedata
from typing import Any


def normalize_category(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if text in {"", "nan", "none", "null", "na", "n/a"}:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.replace("_", " ").replace("-", " ").split())


def truthy_category(value: Any) -> bool:
    return normalize_category(value) in {"1", "true", "si", "yes", "alto", "alta", "recurrente"}
