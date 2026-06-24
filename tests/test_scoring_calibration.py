"""Tests for portfolio risk calibration."""

from __future__ import annotations

import unittest

import pandas as pd

from src.scoring.calibration import TARGET_RISK_DISTRIBUTION, apply_portfolio_calibration


class ScoringCalibrationTests(unittest.TestCase):
    def test_target_distribution_within_tolerance(self) -> None:
        df = pd.DataFrame(
            {
                "score_final": list(range(100)),
                "score_reglas": [10] * 100,
                "rule_trace": [[]] * 100,
            }
        )
        calibrated = apply_portfolio_calibration(df)
        counts = calibrated["nivel_riesgo"].value_counts(normalize=True)
        self.assertAlmostEqual(counts.get("Verde", 0), TARGET_RISK_DISTRIBUTION["verde"], delta=0.05)
        self.assertAlmostEqual(counts.get("Amarillo", 0), TARGET_RISK_DISTRIBUTION["amarillo"], delta=0.05)
        self.assertAlmostEqual(counts.get("Rojo", 0), TARGET_RISK_DISTRIBUTION["rojo"], delta=0.05)

    def test_critical_rules_stay_red(self) -> None:
        df = pd.DataFrame(
            {
                "score_final": [5.0],
                "score_reglas": [10.0],
                "rule_trace": [[{"code": "RF-03", "pdf_ref": "RF-03"}]],
            }
        )
        calibrated = apply_portfolio_calibration(df)
        self.assertEqual(calibrated.iloc[0]["nivel_riesgo"], "Rojo")


if __name__ == "__main__":
    unittest.main()
