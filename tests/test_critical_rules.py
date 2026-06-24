import unittest

from src.rules.rule_registry import evaluate_rules


class CriticalRulesCalibrationTest(unittest.TestCase):
    def test_generic_demo_narrative_does_not_trigger_dynamics_rule(self):
        claim = {
            "id_siniestro": "SIN-GENERIC",
            "ramo": "vehiculos",
            "tipo_impacto": "posterior",
            "descripcion": "Caso crítico demo con patrón repetido en Guayaquil.",
        }

        codes = {rule.code for rule in evaluate_rules(claim)}

        self.assertNotIn("RF-04", codes)

    def test_explicit_impact_contradiction_triggers_dynamics_rule(self):
        claim = {
            "id_siniestro": "SIN-CONTRA",
            "ramo": "vehiculos",
            "tipo_impacto": "posterior",
            "descripcion": "El asegurado declara impacto frontal de frente en intersección.",
        }

        codes = {rule.code for rule in evaluate_rules(claim)}

        self.assertIn("RF-04", codes)

    def test_sercop_signal_is_not_double_counted(self):
        claim = {
            "id_siniestro": "SIN-SERCOP",
            "ramo": "vehiculos",
            "lista_restrictiva_sercop": True,
            "supplier_ruc": "1790000000001",
        }

        codes = [rule.code for rule in evaluate_rules(claim)]

        self.assertIn("RF-03", codes)
        self.assertNotIn("RB-012", codes)

    def test_nlp_similarity_without_clone_marker_does_not_trigger_rf07(self):
        claim = {
            "id_siniestro": "SIN-NLP-GENERIC",
            "ramo": "vehiculos",
            "descripcion": "Sin señales relevantes de riesgo.",
            "alerta_narrativa": True,
            "nivel_alerta_nlp": "alta",
        }

        codes = {rule.code for rule in evaluate_rules(claim)}

        self.assertNotIn("RF-07", codes)

    def test_clone_marker_triggers_rf07(self):
        claim = {
            "id_siniestro": "SIN-NLP-CLONE",
            "ramo": "vehiculos",
            "descripcion": "Reclamo recurrente con narrativa similar y proveedor observado en Quito.",
            "alerta_narrativa": True,
            "nivel_alerta_nlp": "alta",
        }

        codes = {rule.code for rule in evaluate_rules(claim)}

        self.assertIn("RF-07", codes)


if __name__ == "__main__":
    unittest.main()
