import unittest

from src.categorical.normalization import normalize_category, truthy_category
from src.categorical.scoring import build_categorical_signal, enrich_claims_with_categorical
from src.scoring.final_score import score_dataframe


class CategoricalScoringTest(unittest.TestCase):
    def test_normalize_category_removes_accents_and_noise(self):
        self.assertEqual(normalize_category("  Alta-Siniestralidad  "), "alta siniestralidad")
        self.assertEqual(normalize_category("SÍ"), "si")
        self.assertTrue(truthy_category("sí"))
        self.assertFalse(truthy_category("no"))

    def test_build_categorical_signal_explains_risky_values(self):
        claim = {
            "id_siniestro": "SIN-CAT-001",
            "canal_venta": "Referido Externo",
            "estado_poliza": "Mora",
            "tipo_impacto": "Múltiple",
            "documentos_inconsistentes": True,
            "tercero_identificado": False,
            "hay_testigos": False,
            "reporte_policial": False,
        }

        signal = build_categorical_signal(claim)
        fields = {item["field"] for item in signal["senales_categoricas"]}

        self.assertTrue(signal["alerta_categorica"])
        self.assertGreater(signal["score_categorico"], 50)
        self.assertIn("documentos_inconsistentes", fields)
        self.assertIn("canal_venta", fields)
        self.assertIn("tercero_identificado", fields)
        self.assertIn("categoría", signal["explicacion_categorica"].lower())

    def test_enrich_claims_with_categorical_preserves_claim_fields(self):
        claims = [{"id_siniestro": "SIN-1", "estado_poliza": "suspendida"}]
        enriched = enrich_claims_with_categorical(claims)

        self.assertEqual(enriched[0]["id_siniestro"], "SIN-1")
        self.assertIn("score_categorico", enriched[0])
        self.assertTrue(enriched[0]["alerta_categorica"])

    def test_score_dataframe_integrates_categorical_when_pandas_exists(self):
        try:
            import pandas as pd
        except Exception:
            self.skipTest("pandas is not installed in this environment")

        df = pd.DataFrame([
            {
                "id_siniestro": "SIN-1",
                "ramo": "vehiculos",
                "descripcion": "Choque simple.",
                "canal_venta": "Referido Externo",
                "estado_poliza": "Mora",
                "documentos_completos": True,
                "documentos_inconsistentes": False,
                "monto_reclamado": 1000,
                "suma_asegurada": 10000,
            }
        ])

        scored = score_dataframe(df)

        self.assertIn("score_categorico", scored.columns)
        self.assertIn("senales_categoricas", scored.columns)
        self.assertGreater(scored["score_categorico"].iloc[0], 0)


if __name__ == "__main__":
    unittest.main()
