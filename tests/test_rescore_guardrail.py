import unittest
from unittest.mock import patch

import pandas as pd

from src.application.claims import rescore_portfolio
from src.application.claims.rescore_portfolio import rescore_with_population


class _FakeRepo:
    """In-memory stand-in for ScoredClaimsRepository (no disk, no real scoring)."""

    def __init__(self, base: pd.DataFrame, rows: int = 0):
        self._base = base
        self.saved = None

    def read_or_empty(self) -> pd.DataFrame:
        return self._base

    def save(self, df: pd.DataFrame):
        self.saved = df
        return "data/processed/siniestros_scored.csv"


class RescoreGuardrailTest(unittest.TestCase):
    def test_rejects_when_combined_exceeds_limit(self):
        # Population already large; a small upload pushes it over the cap.
        base = pd.DataFrame({"id_siniestro": [f"SIN-{i}" for i in range(10)]})
        repo = _FakeRepo(base)
        new_claims = [{"id_siniestro": f"NEW-{i}"} for i in range(5)]

        with patch.dict("os.environ", {"RASTRO_MAX_SCORING_ROWS": "12"}, clear=False):
            with self.assertRaises(ValueError) as ctx:
                rescore_with_population(new_claims, repository=repo)

        message = str(ctx.exception)
        self.assertIn("máximo de 12", message)
        self.assertIsNone(repo.saved)  # never scored/persisted the oversized batch

    def test_allows_and_scores_when_within_limit(self):
        repo = _FakeRepo(pd.DataFrame())
        new_claims = [{"id_siniestro": "SIN-A"}, {"id_siniestro": "SIN-B"}]

        # Bypass the heavy scoring; we only assert the guardrail lets it through.
        with patch.object(rescore_portfolio, "score_dataframe", side_effect=lambda df: df) as scored:
            with patch.dict("os.environ", {"RASTRO_MAX_SCORING_ROWS": "100"}, clear=False):
                path, total, added = rescore_with_population(new_claims, repository=repo)

        scored.assert_called_once()
        self.assertEqual(added, 2)
        self.assertEqual(total, 2)
        self.assertIsNotNone(repo.saved)


if __name__ == "__main__":
    unittest.main()
