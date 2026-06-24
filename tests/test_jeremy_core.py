import unittest

from src.rules.rule_registry import evaluate_rules, rules_score
from src.scoring.final_score import compute_final_score, score_claim
from src.simulator.simulate_claim import simulate_new_claim


def risky_vehicle_claim():
    return {
        "id_siniestro": "SIN-TEST-001",
        "ramo": "vehiculos",
        "cobertura": "robo total",
        "tipo_evento": "robo total",
        "fecha_inicio_poliza": "2026-01-01",
        "fecha_fin_poliza": "2026-12-31",
        "fecha_ocurrencia": "2026-01-03",
        "fecha_reporte": "2026-01-12",
        "monto_reclamado": 19500,
        "suma_asegurada": 20000,
        "documentos_completos": False,
        "documentos_inconsistentes": True,
        "historial_siniestros_asegurado": 3,
        "historial_siniestros_vehiculo": 3,
        "ocurrio_noche": True,
        "hay_testigos": False,
        "reporte_policial": False,
        "tercero_identificado": False,
        "conductor_recurrente": True,
    }


class JeremyCoreTest(unittest.TestCase):
    def test_rules_emit_traceable_alerts(self):
        results = evaluate_rules(risky_vehicle_claim())
        codes = {result.code for result in results}

        self.assertIn("RB-001", codes)
        self.assertIn("RF-02", codes)
        self.assertNotIn("RB-007", codes)
        self.assertIn("RV-001", codes)
        self.assertTrue(all(result.message for result in results))
        self.assertTrue(all(isinstance(result.evidence, dict) for result in results))
        self.assertGreater(rules_score(results), 70)

    def test_score_claim_outputs_contract_fields(self):
        scored = score_claim(risky_vehicle_claim())

        self.assertGreaterEqual(scored["score_final"], 0)
        self.assertLessEqual(scored["score_final"], 100)
        self.assertEqual(scored["nivel_riesgo"], "Rojo")
        self.assertTrue(scored["alertas_activadas"])
        self.assertIn("priorización", scored["explicacion"])
        self.assertIn("score_reglas", scored)
        self.assertIn("accion_sugerida", scored)

    def test_final_score_uses_neutral_missing_components(self):
        score = compute_final_score({"score_reglas": 100})
        # 30 from rules + 70% of neutral 50 = 65
        self.assertEqual(score, 65)

    def test_simulator_reuses_scoring_engine(self):
        result = simulate_new_claim(risky_vehicle_claim())

        self.assertTrue(result["ok"])
        self.assertTrue(result["simulated"])
        self.assertEqual(result["source"], "simulator")
        self.assertEqual(result["id_siniestro"], "SIN-TEST-001")
        self.assertEqual(result["nivel_riesgo"], "Rojo")
        self.assertEqual(result["risk"]["nivel_riesgo"], "Rojo")
        self.assertTrue(result["alertas"])
        self.assertTrue(result["signals"]["rules"])
        self.assertGreater(result["componentes_score"]["reglas"], 70)
        self.assertEqual(result["ui"]["priority_badge"], "Rojo")
        self.assertIn("historical_claims_loaded", result["context"])

    def test_simulator_normalizes_ui_friendly_aliases(self):
        result = simulate_new_claim({
            "id_siniestro": "SIM-UI-001",
            "ramo": "vehiculo",
            "tipo_evento": "choque",
            "fecha_inicio_poliza": "2026-01-01",
            "fecha_ocurrencia": "2026-01-04",
            "fecha_reporte": "2026-01-12",
            "monto_reclamado": "8500",
            "suma_asegurada": "10000",
            "documentos_presentes": False,
            "proveedor": "PROV-DEMO",
            "narrativa": "Choque al salir del parqueadero sin testigos",
            "ocurrio_noche": "si",
            "hay_testigos": "no",
            "reporte_policial": False,
            "tercero_identificado": False,
        })

        self.assertEqual(result["input_normalizado"]["ramo"], "vehiculos")
        self.assertEqual(result["input_normalizado"]["documentos_completos"], False)
        self.assertEqual(result["input_normalizado"]["id_proveedor"], "PROV-DEMO")
        self.assertEqual(result["input_normalizado"]["descripcion"], "Choque al salir del parqueadero sin testigos")
        self.assertIn(result["risk"]["nivel_riesgo"], {"Verde", "Amarillo", "Rojo"})
        self.assertGreaterEqual(len(result["ui"]["summary_cards"]), 3)


if __name__ == "__main__":
    unittest.main()
