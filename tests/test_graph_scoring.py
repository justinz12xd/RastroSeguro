import unittest

from src.graph.entity_extraction import extract_entities, graph_connections
from src.graph.scoring import enrich_claims_with_graph, score_relationships
from src.scoring.final_score import score_dataframe


class GraphScoringTest(unittest.TestCase):
    def claims(self):
        return [
            {
                "id_siniestro": "SIN-001",
                "ramo": "vehiculos",
                "id_asegurado": "ASE-1",
                "id_proveedor": "PROV-X",
                "beneficiario": "TALLER-X",
                "id_vehiculo": "VEH-1",
                "ciudad": "Quito",
                "cobertura": "choque",
                "descripcion": "Vehículo impactado por tercero.",
                "documentos_completos": True,
                "documentos_inconsistentes": False,
            },
            {
                "id_siniestro": "SIN-002",
                "ramo": "vehiculos",
                "id_asegurado": "ASE-2",
                "id_proveedor": "PROV-X",
                "beneficiario": "TALLER-X",
                "id_vehiculo": "VEH-2",
                "ciudad": "Quito",
                "cobertura": "choque",
                "descripcion": "Choque con tercero no identificado.",
                "documentos_completos": True,
                "documentos_inconsistentes": False,
            },
            {
                "id_siniestro": "SIN-003",
                "ramo": "hogar",
                "id_asegurado": "ASE-3",
                "id_proveedor": "PROV-Y",
                "beneficiario": "BEN-Y",
                "ciudad": "Cuenca",
                "cobertura": "incendio",
                "descripcion": "Daño por incendio en cocina.",
                "documentos_completos": True,
                "documentos_inconsistentes": False,
            },
        ]

    def test_extract_entities_creates_typed_connections(self):
        entities = extract_entities(self.claims()[0])
        keys = {entity.key for entity in entities}

        self.assertIn("proveedor:PROV-X", keys)
        self.assertIn("beneficiario:TALLER-X", keys)
        self.assertIn("vehiculo:VEH-1", keys)
        self.assertTrue(graph_connections(self.claims()[0]))

    def test_score_relationships_detects_recurrent_entities(self):
        signals = score_relationships(self.claims())

        self.assertTrue(signals["SIN-001"]["alerta_red"])
        self.assertGreater(signals["SIN-001"]["score_grafo"], 0)
        recurring_types = {entity["type"] for entity in signals["SIN-001"]["entidades_recurrentes"]}
        self.assertIn("proveedor", recurring_types)
        self.assertIn("beneficiario", recurring_types)
        self.assertFalse(signals["SIN-003"]["alerta_red"])

    def test_enrich_claims_with_graph_sets_rule_flags(self):
        enriched = enrich_claims_with_graph(self.claims())
        first = enriched[0]

        self.assertTrue(first["proveedor_recurrente"])
        self.assertTrue(first["beneficiario_recurrente"])
        self.assertIn("conexiones_grafo", first)
        self.assertIn("explicacion_grafo", first)

    def test_score_dataframe_integrates_graph_when_pandas_exists(self):
        try:
            import pandas as pd
        except Exception:
            self.skipTest("pandas is not installed in this environment")

        df = pd.DataFrame(self.claims())
        scored = score_dataframe(df)

        self.assertIn("score_grafo", scored.columns)
        self.assertIn("entidades_recurrentes", scored.columns)
        self.assertTrue(scored.loc[scored["id_siniestro"] == "SIN-001", "proveedor_recurrente"].iloc[0])


if __name__ == "__main__":
    unittest.main()
