"""Parity tests for unified claim signal engine."""

from __future__ import annotations

import unittest

import pandas as pd

from pipelines.data.claim_signals import (
    apply_signals_to_frame,
    compute_signal_masks,
    signal_coverage,
    signal_coverage_from_masks,
)
from src.data.portfolio_stats import PortfolioStats


def _mini_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id_proveedor": "PROV-001",
                "beneficiario": "Ben A",
                "ramo": "vehiculos",
                "dias_desde_inicio_poliza": 5,
                "dias_desde_fin_poliza": 100,
                "dias_entre_ocurrencia_reporte": 10,
                "documentos_inconsistentes": True,
                "monto_reclamado": 9000,
                "suma_asegurada": 10000,
                "historial_siniestros_asegurado": 3,
                "historial_siniestros_vehiculo": 2,
                "conductor_recurrente": True,
                "tercero_identificado": False,
            },
            {
                "id_proveedor": "PROV-002",
                "beneficiario": "Ben B",
                "ramo": "salud",
                "dias_desde_inicio_poliza": 200,
                "dias_desde_fin_poliza": 200,
                "dias_entre_ocurrencia_reporte": 2,
                "documentos_inconsistentes": False,
                "monto_reclamado": 100,
                "suma_asegurada": 10000,
                "historial_siniestros_asegurado": 0,
                "historial_siniestros_vehiculo": 0,
                "conductor_recurrente": False,
                "tercero_identificado": True,
            },
        ]
    )


class ClaimSignalsTests(unittest.TestCase):
    def test_apply_matches_coverage(self) -> None:
        df = _mini_frame()
        stats = PortfolioStats.from_frame(df)
        applied = apply_signals_to_frame(df, stats=stats)
        masks = compute_signal_masks(df, stats=stats)
        coverage = signal_coverage_from_masks(masks)
        direct = signal_coverage(df, stats=stats)
        self.assertEqual(coverage, direct)
        for name, ratio in coverage.items():
            col = f"signal_{name}"
            self.assertAlmostEqual(float(applied[col].mean()), ratio, places=4)

    def test_shared_stats_recurrence(self) -> None:
        repeated = pd.concat([_mini_frame()] * 10, ignore_index=True)
        repeated["id_proveedor"] = "PROV-SAME"
        stats = PortfolioStats.from_frame(repeated)
        enriched = stats.enrich_frame(repeated)
        self.assertTrue(enriched["proveedor_recurrente"].all())


if __name__ == "__main__":
    unittest.main()
