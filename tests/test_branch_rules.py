import unittest

from src.rules.rule_registry import evaluate_rules
from src.scoring.final_score import score_claim


class BranchRulesTest(unittest.TestCase):
    def assert_rule_codes(self, claim, expected_codes):
        results = evaluate_rules(claim)
        codes = {result.code for result in results}
        for code in expected_codes:
            self.assertIn(code, codes)
        self.assertTrue(all(result.message for result in results))
        self.assertTrue(all(result.evidence for result in results))

    def test_health_rules_emit_medical_signals(self):
        claim = {
            "id_siniestro": "SAL-001",
            "ramo": "salud",
            "fecha_ocurrencia": "2026-03-01",
            "fecha_reporte": "2026-03-10",
            "monto_reclamado": 3000,
            "monto_promedio_procedimiento": 1500,
            "suma_asegurada": 5000,
            "documentos_completos": True,
            "documentos_inconsistentes": False,
            "frecuencia_atenciones": 4,
            "proveedor_medico_recurrente": True,
            "fecha_atencion": "2026-03-10",
            "fecha_factura": "2026-03-05",
        }
        self.assert_rule_codes(claim, {"RS-001", "RS-002", "RS-003", "RS-004"})
        self.assertGreater(score_claim(claim)["score_reglas"], 30)

    def test_home_rules_emit_property_signals(self):
        claim = {
            "id_siniestro": "HOG-001",
            "ramo": "hogar",
            "fecha_ocurrencia": "2026-02-01",
            "fecha_reporte": "2026-02-12",
            "monto_reclamado": 9000,
            "suma_asegurada": 10000,
            "documentos_completos": False,
            "documentos_inconsistentes": False,
            "inspeccion_realizada": False,
            "proveedor_reparacion_recurrente": True,
            "danios_repetidos_periodo": 2,
            "causa_reportada": "incendio",
            "evidencia_fotografica": False,
        }
        self.assert_rule_codes(claim, {"RH-001", "RH-002", "RH-003", "RH-004"})
        self.assertGreater(score_claim(claim)["score_reglas"], 30)

    def test_life_rules_emit_beneficiary_signals(self):
        claim = {
            "id_siniestro": "VID-001",
            "ramo": "vida",
            "fecha_ocurrencia": "2026-01-01",
            "fecha_reporte": "2026-02-10",
            "monto_reclamado": 50000,
            "suma_asegurada": 50000,
            "documentos_completos": True,
            "documentos_inconsistentes": False,
            "beneficiario_recurrente": True,
            "cambios_recientes_poliza": 1,
            "fecha_evento": "2026-01-01",
            "fecha_notificacion": "2026-02-10",
            "documento_soporte": False,
        }
        self.assert_rule_codes(claim, {"RL-001", "RL-002", "RL-003", "RL-004"})
        self.assertGreaterEqual(score_claim(claim)["score_reglas"], 40)

    def test_general_rules_emit_coverage_signals(self):
        claim = {
            "id_siniestro": "GEN-001",
            "ramo": "generales",
            "fecha_ocurrencia": "2026-04-01",
            "fecha_reporte": "2026-04-09",
            "monto_reclamado": 9000,
            "monto_promedio_cobertura": 4000,
            "suma_asegurada": 10000,
            "documentos_completos": True,
            "documentos_inconsistentes": True,
            "intermediario_recurrente": True,
            "inconsistencia_cobertura": True,
        }
        self.assert_rule_codes(claim, {"RG-001", "RG-002", "RG-003"})
        self.assertGreater(score_claim(claim)["score_reglas"], 30)


if __name__ == "__main__":
    unittest.main()
