import unittest

from src.graph.fraud_rings import detect_fraud_rings


class FraudRingsTest(unittest.TestCase):
    def sample_claims(self):
        return [
            {
                "id_siniestro": "SIN-001",
                "ramo": "vehiculos",
                "id_asegurado": "ASE-1",
                "id_proveedor": "PROV-X",
                "beneficiario": "TALLER-X",
                "taller": "TALLER-X",
                "id_vehiculo": "VEH-1",
                "nivel_riesgo": "Amarillo",
                "score_final": 55,
                "monto_reclamado": 5000,
            },
            {
                "id_siniestro": "SIN-002",
                "ramo": "vehiculos",
                "id_asegurado": "ASE-2",
                "id_proveedor": "PROV-X",
                "beneficiario": "TALLER-X",
                "taller": "TALLER-X",
                "id_vehiculo": "VEH-2",
                "nivel_riesgo": "Rojo",
                "score_final": 82,
                "monto_reclamado": 9000,
            },
            {
                "id_siniestro": "SIN-003",
                "ramo": "vehiculos",
                "id_asegurado": "ASE-3",
                "id_proveedor": "PROV-X",
                "beneficiario": "TALLER-X",
                "taller": "TALLER-X",
                "id_vehiculo": "VEH-3",
                "nivel_riesgo": "Rojo",
                "score_final": 78,
                "monto_reclamado": 7000,
            },
            {
                "id_siniestro": "SIN-999",
                "ramo": "hogar",
                "id_asegurado": "ASE-9",
                "id_proveedor": "PROV-Z",
                "beneficiario": "BEN-Z",
                "nivel_riesgo": "Verde",
                "score_final": 20,
                "monto_reclamado": 1000,
            },
        ]

    def test_detects_ring_of_three_connected_claims(self):
        result = detect_fraud_rings(self.sample_claims(), limit=5)
        self.assertGreaterEqual(result["total_anillos"], 1)
        top_ring = result["anillos"][0]
        self.assertEqual(top_ring["tamano"], 3)
        self.assertEqual(set(top_ring["siniestros"]), {"SIN-001", "SIN-002", "SIN-003"})
        self.assertGreaterEqual(top_ring["casos_rojos"], 2)
        self.assertGreater(top_ring["ring_risk_score"], 0)
        shared_types = {entity["type"] for entity in top_ring["entidades_compartidas"]}
        self.assertIn("proveedor", shared_types)
        self.assertIn("beneficiario", shared_types)

    def test_isolated_claim_does_not_form_ring(self):
        result = detect_fraud_rings(self.sample_claims(), limit=10)
        all_members = {cid for ring in result["anillos"] for cid in ring["siniestros"]}
        self.assertNotIn("SIN-999", all_members)

    def test_ring_explanation_mentions_ethical_framing(self):
        result = detect_fraud_rings(self.sample_claims(), limit=1)
        explanation = result["anillos"][0]["explicacion"].lower()
        self.assertIn("revisión humana", explanation)


if __name__ == "__main__":
    unittest.main()
