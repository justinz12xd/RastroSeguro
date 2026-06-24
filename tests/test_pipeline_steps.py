"""Tests for modular Carlos pipeline steps."""

from __future__ import annotations

import unittest

import pandas as pd

from pipelines.models.pipeline_steps import sample_scoring_window


class PipelineStepsTests(unittest.TestCase):
    def test_sample_scoring_window_respects_limit(self) -> None:
        df = pd.DataFrame(
            {
                "id_siniestro": [f"SIN-{i:03d}" for i in range(100)],
                "etiqueta_fraude_simulada": [1 if i % 5 == 0 else 0 for i in range(100)],
            }
        )
        sampled = sample_scoring_window(df, 20)
        self.assertEqual(len(sampled), 20)
        self.assertTrue(sampled["etiqueta_fraude_simulada"].astype(int).sum() >= 1)

    def test_sample_returns_full_when_disabled(self) -> None:
        df = pd.DataFrame({"id_siniestro": ["SIN-001"], "etiqueta_fraude_simulada": [0]})
        self.assertEqual(len(sample_scoring_window(df, 0)), 1)


if __name__ == "__main__":
    unittest.main()
