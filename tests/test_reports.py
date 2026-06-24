import unittest

from src.reports.executive_summary import build_executive_report
from src.reports.markdown_report import render_markdown_report
from src.reports.sections import aggregate_by_field, exposed_amount, risk_counts, top_claims


class ReportsTest(unittest.TestCase):
    def claims(self):
        return [
            {
                "id_siniestro": "SIN-001",
                "ramo": "vehiculos",
                "ciudad": "Quito",
                "id_proveedor": "PROV-A",
                "score_final": 92,
                "nivel_riesgo": "Rojo",
                "monto_reclamado": 10000,
                "accion_sugerida": "Escalar.",
            },
            {
                "id_siniestro": "SIN-002",
                "ramo": "salud",
                "ciudad": "Quito",
                "id_proveedor": "PROV-A",
                "score_final": 70,
                "nivel_riesgo": "Amarillo",
                "monto_reclamado": 3000,
                "accion_sugerida": "Revisar.",
            },
            {
                "id_siniestro": "SIN-003",
                "ramo": "hogar",
                "ciudad": "Cuenca",
                "id_proveedor": "PROV-B",
                "score_final": 30,
                "nivel_riesgo": "Verde",
                "monto_reclamado": 1500,
                "accion_sugerida": "Continuar.",
            },
        ]

    def test_sections_summarize_claims(self):
        claims = self.claims()

        self.assertEqual(risk_counts(claims), {"Verde": 1, "Amarillo": 1, "Rojo": 1})
        self.assertEqual(top_claims(claims, limit=1)[0]["id_siniestro"], "SIN-001")
        self.assertEqual(exposed_amount(claims, "Rojo"), 10000)
        self.assertEqual(aggregate_by_field(claims, "id_proveedor")[0]["id_proveedor"], "PROV-A")

    def test_build_executive_report_contract(self):
        report = build_executive_report(self.claims(), top_limit=2)

        self.assertEqual(report["summary"]["total_siniestros"], 3)
        self.assertEqual(report["summary"]["casos_rojos"], 1)
        self.assertEqual(len(report["top_casos"]), 2)
        self.assertIn("ethics_note", report)
        self.assertIn("top_proveedores", report)

    def test_render_markdown_report_contains_demo_sections(self):
        markdown = render_markdown_report(build_executive_report(self.claims()))

        self.assertIn("# Reporte ejecutivo", markdown)
        self.assertIn("## Top casos críticos", markdown)
        self.assertIn("## Nota ética", markdown)
        self.assertIn("SIN-001", markdown)
        self.assertIn("no acusa fraude", markdown.lower())


if __name__ == "__main__":
    unittest.main()

class DemoDifferentiatorsTest(unittest.TestCase):
    def test_claim_dossier_and_business_impact_are_jury_ready(self):
        import json
        import tempfile
        from pathlib import Path

        import pandas as pd

        from src.reports.demo_differentiators import build_business_impact, build_claim_dossier, build_star_case_catalog

        rows = [
            {
                "id_siniestro": "SIN-900",
                "ramo": "vehiculos",
                "cobertura": "robo",
                "ciudad": "Quito",
                "id_asegurado": "ASEG-1",
                "id_proveedor": "PROV-A",
                "beneficiario": "Taller A",
                "monto_reclamado": 9500,
                "suma_asegurada": 10000,
                "fecha_ocurrencia": "2026-01-02",
                "fecha_reporte": "2026-01-08",
                "score_final": 91,
                "nivel_riesgo": "Rojo",
                "score_reglas": 88,
                "score_modelo": 70,
                "score_anomalia": 65,
                "score_nlp": 80,
                "score_grafo": 75,
                "score_categorico": 50,
                "alerta_narrativa": True,
                "alertas_activadas": json.dumps([
                    {"code": "RB-001", "name": "Borde de vigencia", "points": 8, "severity": "alta", "message": "Ocurrió cerca del inicio.", "evidence": {"dias": 2}}
                ]),
                "siniestros_similares": json.dumps([{"id_siniestro": "SIN-901", "similaridad": 0.91}]),
                "conexiones_grafo": json.dumps([{"entity": "PROV-A", "type": "proveedor"}]),
                "entidades_recurrentes": json.dumps([{"entity": "PROV-A", "count": 3}]),
                "explicacion_nlp": "Narrativa similar a otro reclamo.",
                "explicacion_grafo": "Proveedor recurrente en la red.",
                "accion_sugerida": "Escalar a revisión.",
                "explicacion": "Priorización para revisión humana.",
            },
            {
                "id_siniestro": "SIN-901",
                "ramo": "hogar",
                "cobertura": "incendio",
                "ciudad": "Cuenca",
                "id_asegurado": "ASEG-2",
                "id_proveedor": "PROV-A",
                "monto_reclamado": 2000,
                "suma_asegurada": 10000,
                "score_final": 62,
                "nivel_riesgo": "Amarillo",
                "score_reglas": 30,
                "score_modelo": 55,
                "score_anomalia": 55,
                "score_nlp": 68,
                "score_grafo": 68,
                "score_categorico": 50,
                "alerta_narrativa": True,
                "alertas_activadas": "[]",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scored.csv"
            pd.DataFrame(rows).to_csv(path, index=False)
            dossier = build_claim_dossier("SIN-900", data_path=path)
            impact = build_business_impact(data_path=path, review_percent=0.5)
            stars = build_star_case_catalog(data_path=path)

        self.assertEqual(dossier["risk"]["decision_automatica"], "No")
        self.assertEqual(dossier["claim"]["ratio_monto_suma"], 0.95)
        self.assertTrue(dossier["evidence"])
        self.assertTrue(dossier["timeline"])
        self.assertTrue(dossier["signal_radar"])
        self.assertIn("investigation_summary", dossier)
        self.assertIn("executive_takeaway", dossier)
        self.assertEqual(dossier["similar_cases_summary"]["similar_cases"][0]["id_siniestro"], "SIN-901")
        self.assertIn("alerta", dossier["ethical_guardrail"].lower())
        self.assertEqual(impact["casos_a_revisar_top_percent"], 1)
        self.assertIn("exposición", impact["mensaje"])
        self.assertGreaterEqual(stars["count"], 2)
