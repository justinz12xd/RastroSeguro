import unittest

from src.nlp.narrative_signals import classify_similarity
from src.nlp.scoring import enrich_claims_with_nlp, score_narratives
from src.nlp.text_normalization import normalized_for_vectorizer, tokenize
from src.scoring.final_score import score_dataframe


class NarrativeScoringTest(unittest.TestCase):
    def test_text_normalization_keeps_domain_meaning(self):
        text = "Mi vehículo fue impactado por un auto desconocido que huyó."
        tokens = tokenize(text)

        self.assertIn("vehiculo", tokens)
        self.assertIn("choque", tokens)
        self.assertIn("no_identificado", tokens)
        self.assertIn("huye", tokens)
        self.assertNotIn("mi", tokens)
        self.assertEqual(normalized_for_vectorizer("Auto colisionó y escapó"), "vehiculo choque huye")

    def test_classify_similarity_pdf_bands(self):
        self.assertEqual(classify_similarity(0.86), (8, "alta"))
        self.assertEqual(classify_similarity(0.72), (4, "media"))

    def test_score_narratives_detects_similar_claims(self):
        claims = [
            {
                "id_siniestro": "SIN-001",
                "descripcion": "Vehículo desconocido impactó mi auto y huyó del lugar.",
            },
            {
                "id_siniestro": "SIN-002",
                "descripcion": "Auto no identificado colisionó el vehículo y escapó del sitio.",
            },
            {
                "id_siniestro": "SIN-003",
                "descripcion": "Daño por filtración de agua en la cocina del inmueble.",
            },
        ]

        signals = score_narratives(claims, threshold=0.30)

        similar_ids = {item["target_id"] for item in signals["SIN-001"]["siniestros_similares"]}
        self.assertIn("SIN-002", similar_ids)
        if signals["SIN-001"]["siniestros_similares"]:
            best_sim = signals["SIN-001"]["siniestros_similares"][0]["similarity"]
            if best_sim >= 0.70:
                self.assertTrue(signals["SIN-001"]["alerta_narrativa"])
        self.assertFalse(signals["SIN-003"]["alerta_narrativa"])

    def test_enrich_claims_adds_nlp_contract_fields(self):
        claims = [
            {"id_siniestro": "SIN-001", "descripcion": "Vehículo desconocido chocó y huyó."},
            {"id_siniestro": "SIN-002", "descripcion": "Auto no identificado impactó y escapó."},
        ]

        enriched = enrich_claims_with_nlp(claims, threshold=0.25)

        for claim in enriched:
            self.assertIn("score_nlp", claim)
            self.assertIn("siniestros_similares", claim)
            self.assertIn("explicacion_nlp", claim)

    def test_score_dataframe_integrates_nlp_when_descriptions_exist(self):
        try:
            import pandas as pd
        except Exception:
            self.skipTest("pandas is not installed in this environment")

        df = pd.DataFrame([
            {
                "id_siniestro": "SIN-001",
                "ramo": "vehiculos",
                "descripcion": "Vehículo desconocido chocó y huyó.",
                "fecha_ocurrencia": "2026-01-01",
                "fecha_reporte": "2026-01-02",
                "monto_reclamado": 1000,
                "suma_asegurada": 10000,
                "documentos_completos": True,
                "documentos_inconsistentes": False,
            },
            {
                "id_siniestro": "SIN-002",
                "ramo": "vehiculos",
                "descripcion": "Auto no identificado impactó y escapó.",
                "fecha_ocurrencia": "2026-01-01",
                "fecha_reporte": "2026-01-02",
                "monto_reclamado": 1200,
                "suma_asegurada": 10000,
                "documentos_completos": True,
                "documentos_inconsistentes": False,
            },
        ])

        scored = score_dataframe(df)

        self.assertIn("score_nlp", scored.columns)
        self.assertIn("siniestros_similares", scored.columns)


if __name__ == "__main__":
    unittest.main()
