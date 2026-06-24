"""Entity extraction from user questions."""

from __future__ import annotations

import re

CLAIM_ID_PATTERN = re.compile(r"\bSIN[-_]?\d+\b", re.IGNORECASE)
LIMIT_PATTERN = re.compile(r"\b(?:top|primeros|primeras)?\s*(\d{1,3})\b", re.IGNORECASE)


def extract_claim_id(text: str) -> str | None:
    match = CLAIM_ID_PATTERN.search(text)
    if not match:
        return None
    return match.group(0).upper().replace("_", "-")


def extract_limit(text: str, default: int = 10, maximum: int = 50) -> int:
    match = LIMIT_PATTERN.search(text)
    if not match:
        return default
    return max(1, min(maximum, int(match.group(1))))
