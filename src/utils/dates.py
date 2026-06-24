"""Date parsing helpers used by rules and simulators."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def parse_date(value: Any) -> date | None:
    """Parse common date representations into a date.

    Returns None for missing or invalid values so rules can skip gracefully.
    """
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def days_between(start: Any, end: Any) -> int | None:
    start_date = parse_date(start)
    end_date = parse_date(end)
    if not start_date or not end_date:
        return None
    return (end_date - start_date).days
