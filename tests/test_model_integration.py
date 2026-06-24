import unittest

from src.model_integration.features import align_records, select_feature_columns
from src.model_integration.predictors import anomaly_scores, classifier_scores
from src.model_integration.scoring import enrich_claims_with_loaded_models, enrich_claims_with_model_scores
from src.scoring.final_score import score_dataframe


class FakeClassifier:
    def predict_proba(self, records):
        records_list = records.to_dict(orient="records") if hasattr(records, "to_dict") else records
        return [[0.15, 0.85] if record.get("monto_reclamado", 0) > 5000 else [0.80, 0.20] for record in records_list]


class FakeAnomaly:
    def predict(self, records):
        records_list = records.to_dict(orient="records") if hasattr(records, "to_dict") else records
        return [-1 if record.get("monto_reclamado", 0) > 5000 else 1 for record in records_list]


class ModelIntegrationTest(unittest.TestCase):
    def claims(self):
        return [
            {"id_siniestro": "SIN-1", "monto_reclamado": 8000, "suma_asegurada": 10000, "ramo": "vehiculos"},
            {"id_siniestro": "SIN-2", "monto_reclamado": 1000, "suma_asegurada": 10000, "ramo": "hogar"},
        ]

    def test_select_and_align_feature_columns(self):
        columns = select_feature_columns(self.claims(), configured=["monto_reclamado", "score_reglas"])
        aligned = align_records(self.claims(), columns)

        self.assertEqual(columns, ["monto_reclamado", "score_reglas"])
        self.assertEqual(aligned[0]["monto_reclamado"], 8000)
        self.assertEqual(aligned[0]["score_reglas"], 0)

    def test_predictor_adapters_convert_outputs_to_scores(self):
        records = self.claims()

        self.assertEqual(classifier_scores(FakeClassifier(), records), [85.0, 20.0])
        self.assertEqual(anomaly_scores(FakeAnomaly(), records), [80.0, 20.0])

    def test_missing_artifacts_set_neutral_scores(self):
        from pathlib import Path
        enriched = enrich_claims_with_model_scores(
            self.claims(),
            classifier_path=Path("nonexistent_classifier.joblib"),
            anomaly_path=Path("nonexistent_anomaly.joblib")
        )

        self.assertEqual(enriched[0]["score_modelo"], 50.0)
        self.assertEqual(enriched[0]["score_anomalia"], 50.0)
        self.assertFalse(enriched[0]["modelo_disponible"])
        self.assertFalse(enriched[0]["anomalia_disponible"])

    def test_loaded_models_set_scores_and_metadata(self):
        classifier_artifact = {"model": FakeClassifier(), "feature_columns": ["monto_reclamado"]}
        anomaly_artifact = {"model": FakeAnomaly(), "feature_columns": ["monto_reclamado"]}

        enriched = enrich_claims_with_loaded_models(self.claims(), classifier_artifact, anomaly_artifact)

        self.assertEqual(enriched[0]["score_modelo"], 85.0)
        self.assertEqual(enriched[0]["score_anomalia"], 80.0)
        self.assertTrue(enriched[0]["modelo_disponible"])
        self.assertEqual(enriched[0]["modelo_features"], ["monto_reclamado"])

    def test_score_dataframe_integrates_model_columns_when_pandas_exists(self):
        try:
            import pandas as pd
        except Exception:
            self.skipTest("pandas is not installed in this environment")

        df = pd.DataFrame(self.claims())
        scored = score_dataframe(df)

        self.assertIn("score_modelo", scored.columns)
        self.assertIn("score_anomalia", scored.columns)
        self.assertIn("modelo_disponible", scored.columns)


if __name__ == "__main__":
    unittest.main()
