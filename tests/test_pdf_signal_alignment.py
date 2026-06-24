"""Tests for PDF §7–§8 signal alignment."""

import unittest

from src.nlp.narrative_signals import classify_similarity
from src.rules.common.document_rules import evaluate_document_rules
from src.rules.critical_rules import evaluate_critical_rules
from src.rules.vehicle_rules import evaluate_vehicle_rules


class PdfSignalAlignmentTest(unittest.TestCase):
    def test_nlp_thresholds_pdf_bands(self):
        self.assertEqual(classify_similarity(0.90), (8, "alta"))
        self.assertEqual(classify_similarity(0.85), (8, "alta"))
        self.assertEqual(classify_similarity(0.75), (4, "media"))
        self.assertEqual(classify_similarity(0.70), (4, "media"))
        self.assertEqual(classify_similarity(0.69), (0, "sin_alerta"))

    def test_rf02_emitted_without_rb007_duplicate(self):
        claim = {"documentos_inconsistentes": True, "documentos_completos": True}
        critical = evaluate_critical_rules(claim)
        docs = evaluate_document_rules(claim)
        codes_critical = {r.code for r in critical}
        codes_docs = {r.code for r in docs}
        self.assertIn("RF-02", codes_critical)
        self.assertNotIn("RB-007", codes_docs)

    def test_rv009_robo_delay_hours(self):
        claim = {
            "ramo": "vehiculos",
            "cobertura": "robo",
            "tipo_evento": "robo",
            "dias_entre_ocurrencia_reporte": 3,
            "tercero_identificado": True,
            "reporte_policial": True,
        }
        results = evaluate_vehicle_rules(claim)
        rv9 = [r for r in results if r.code == "RV-009"]
        self.assertEqual(len(rv9), 1)
        self.assertEqual(rv9[0].points, 8)

    def test_rv011_multiple_night_accident(self):
        claim = {
            "ramo": "vehiculos",
            "cobertura": "choque",
            "tipo_evento": "multiple",
            "descripcion": "Accidente múltiple en intersección",
            "ocurrio_noche": True,
            "tercero_identificado": True,
            "reporte_policial": True,
            "historial_siniestros_vehiculo": 0,
        }
        results = evaluate_vehicle_rules(claim)
        codes = {r.code for r in results}
        self.assertIn("RV-011", codes)


if __name__ == "__main__":
    unittest.main()
