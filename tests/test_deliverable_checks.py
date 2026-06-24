"""Tests for modular deliverable validation checks."""

from __future__ import annotations

import unittest

import pandas as pd

from pipelines.models.deliverable_checks import check_benchmark_questions, check_dataset_schema, check_star_cases


class DeliverableChecksTests(unittest.TestCase):
    def test_schema_detects_missing_columns(self) -> None:
        df = pd.DataFrame({"id_siniestro": ["SIN-001"]})
        errors = check_dataset_schema(df, ["id_siniestro", "ramo"], [], [])
        self.assertTrue(any("ramo" in err for err in errors))

    def test_benchmark_requires_twelve_questions(self) -> None:
        errors, summary = check_benchmark_questions({"questions": [{}] * 5})
        self.assertTrue(errors)
        self.assertEqual(summary["benchmark_questions"], 5)

    def test_star_cases_require_red_and_yellow(self) -> None:
        errors, _ = check_star_cases({"cases": [{"nivel_riesgo": "Rojo"}]})
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
