"""Persistence boundary for the scored-claims portfolio.

Today the portfolio is a CSV file on disk. Centralising read/write here means
the storage backend can later change (SQLite, Postgres, object storage) without
touching routes, tools, or domain code — they depend on this interface, not on
``pandas.read_csv``/``to_csv`` against a hardcoded path.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.infrastructure.config.paths import SCORED_CLAIMS_PATH


class ScoredClaimsRepository:
    """Read/write access to the scored portfolio."""

    def __init__(self, path: Path = SCORED_CLAIMS_PATH) -> None:
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def read(self) -> pd.DataFrame:
        """Read the scored portfolio. Raises FileNotFoundError if absent."""
        return pd.read_csv(self.path)

    def read_or_empty(self) -> pd.DataFrame:
        """Read the scored portfolio, or an empty frame if it does not exist."""
        return pd.read_csv(self.path) if self.path.exists() else pd.DataFrame()

    def save(self, df: pd.DataFrame) -> Path:
        """Persist the scored portfolio, creating parent dirs as needed."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.path, index=False)
        return self.path
