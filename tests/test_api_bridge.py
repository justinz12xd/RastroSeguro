import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import create_app


class ApiBridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.env_patch = patch.dict(
            "os.environ",
            {"RASTRO_AGENT_HISTORY_DB": str(Path(self.temp_dir.name) / "chat_history.sqlite")},
            clear=False,
        )
        self.env_patch.start()
        self.client = TestClient(create_app())

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_healthcheck_uses_standard_envelope(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["service"], "rastroseguro-api")
        self.assertIsNone(payload["error"])

    def test_claims_endpoint_wraps_tool_data(self):
        with patch("api.routes.claims.tools.get_top_risky_claims", return_value=[{"id_siniestro": "SIN-1"}]) as tool:
            response = self.client.get("/api/claims?limit=5")

        tool.assert_called_once_with(limit=5)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"], [{"id_siniestro": "SIN-1"}])

    def test_missing_scored_file_becomes_actionable_error(self):
        with patch("api.routes.claims.tools.get_top_risky_claims", side_effect=FileNotFoundError("missing csv")):
            response = self.client.get("/api/claims")

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertIsNone(payload["data"])
        self.assertIn("missing csv", payload["error"]["message"])
        self.assertIn("scoring", payload["error"]["hint"])

    def test_explanation_endpoint_calls_explain_claim(self):
        with patch("api.routes.claims.explain_claim", return_value={"id_siniestro": "SIN-9", "score_final": 88}) as explain:
            response = self.client.get("/api/claims/SIN-9/explanation")

        explain.assert_called_once_with("SIN-9")
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["data"]["score_final"], 88)

    def test_dossier_endpoint_calls_tool(self):
        with patch("api.routes.claims.tools.get_claim_dossier", return_value={"id_siniestro": "SIN-9", "headline": "Expediente"}) as tool:
            response = self.client.get("/api/claims/SIN-9/dossier")

        tool.assert_called_once_with("SIN-9")
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["headline"], "Expediente")

    def test_star_cases_endpoint_calls_tool(self):
        with patch("api.routes.reports.tools.get_demo_star_cases", return_value={"count": 1, "cases": []}) as tool:
            response = self.client.get("/api/reports/star-cases")

        tool.assert_called_once_with()
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["count"], 1)

    def test_business_impact_endpoint_accepts_review_percent(self):
        with patch("api.routes.reports.tools.get_business_impact", return_value={"mensaje": "exposicion"}) as tool:
            response = self.client.get("/api/reports/business-impact?review_percent=0.2")

        tool.assert_called_once_with(review_percent=0.2)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertIn("exposicion", payload["data"]["mensaje"])

    def test_fraud_rings_endpoint_calls_tool(self):
        payload_data = {"total_anillos": 1, "anillos": [{"id_anillo": "RING-001"}], "explicacion_global": "ok"}
        with patch("api.routes.reports.tools.get_fraud_rings", return_value=payload_data) as tool:
            response = self.client.get("/api/graph/fraud-rings?limit=5")

        tool.assert_called_once_with(limit=5)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["total_anillos"], 1)

    def test_simulator_endpoint_accepts_direct_claim_payload(self):
        simulated = {"ok": True, "simulated": True, "risk": {"nivel_riesgo": "Rojo"}}
        with patch("api.routes.simulator.simulate_new_claim", return_value=simulated) as simulate:
            response = self.client.post("/api/simulator/claim", json={"ramo": "vehiculo"})

        simulate.assert_called_once_with({"ramo": "vehiculo"})
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["data"]["simulated"])

    def test_agent_endpoint_wraps_success_response(self):
        agent_response = {"ok": True, "message": "Respuesta", "source": "tools"}
        with patch("api.routes.agent.answer_question", return_value=agent_response) as answer:
            response = self.client.post("/api/agent/ask", json={"question": "top casos", "selected_claim_id": "SIN-0099"})

        answer.assert_called_once_with(
            "top casos",
            history=None,
            selected_claim_id="SIN-0099",
            runtime="langgraph",
            user_role="analyst",
        )
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["message"], "Respuesta")

    def test_agent_chat_persists_thread_and_returns_history(self):
        agent_response = {
            "ok": True,
            "intent": "ranking_proveedores",
            "message": "Respuesta persistida",
            "data": [{"id_proveedor": "PROV-9"}],
            "source": "tools",
            "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
            "context": {"resolved_claim_id": "SIN-0045"},
            "llm": {"status": "disabled_by_config"},
        }
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            response = self.client.post(
                "/api/agent/chat",
                json={"message": "Explica SIN-0045", "selected_claim_id": "SIN-0045"},
            )

        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertIsNotNone(payload["data"]["thread_id"])
        self.assertEqual(len(payload["data"]["history"]), 2)
        self.assertEqual(payload["data"]["history"][0]["role"], "user")
        self.assertEqual(payload["data"]["history"][1]["intent"], "ranking_proveedores")

    def test_agent_thread_endpoint_recovers_persisted_history(self):
        agent_response = {
            "ok": True,
            "intent": "top_riesgo",
            "message": "Casos priorizados",
            "data": [],
            "source": "tools",
            "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
            "context": {"resolved_claim_id": None},
            "llm": {"status": "disabled_by_config"},
        }
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            create_response = self.client.post("/api/agent/chat", json={"message": "top casos"})

        thread_id = create_response.json()["data"]["thread_id"]
        response = self.client.get(f"/api/agent/threads/{thread_id}")
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["thread_id"], thread_id)
        self.assertEqual(len(payload["data"]["history"]), 2)

    def test_agent_chat_rejects_foreign_thread_for_another_user(self):
        agent_response = {
            "ok": True,
            "intent": "top_riesgo",
            "message": "Casos priorizados",
            "data": [],
            "source": "tools",
            "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
            "context": {"resolved_claim_id": None},
            "llm": {"status": "disabled_by_config"},
        }
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            create_response = self.client.post(
                "/api/agent/chat",
                json={"user_id": "analyst-a", "message": "top casos"},
            )
        thread_id = create_response.json()["data"]["thread_id"]

        response = self.client.post(
            "/api/agent/chat",
            json={"user_id": "analyst-b", "thread_id": thread_id, "message": "intento ajeno"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertIn("thread", payload["error"]["message"].lower())

    def test_agent_sessions_are_scoped_by_user(self):
        agent_response = {
            "ok": True,
            "intent": "top_riesgo",
            "message": "Casos priorizados",
            "data": [],
            "source": "tools",
            "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
            "context": {"resolved_claim_id": None},
            "llm": {"status": "disabled_by_config"},
        }
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            self.client.post("/api/agent/chat", json={"user_id": "analyst-a", "message": "top casos"})
            self.client.post("/api/agent/chat", json={"user_id": "analyst-b", "message": "top proveedores"})

        response_a = self.client.get("/api/agent/sessions?user_id=analyst-a")
        response_b = self.client.get("/api/agent/sessions?user_id=analyst-b")
        sessions_a = response_a.json()["data"]
        sessions_b = response_b.json()["data"]
        self.assertEqual(len(sessions_a), 1)
        self.assertEqual(len(sessions_b), 1)
        self.assertEqual(sessions_a[0]["user_id"], "analyst-a")
        self.assertEqual(sessions_b[0]["user_id"], "analyst-b")
        self.assertNotEqual(sessions_a[0]["thread_id"], sessions_b[0]["thread_id"])

    def test_agent_chat_groups_messages_into_sections(self):
        responses = [
            {
                "ok": True,
                "intent": "explicar_siniestro",
                "message": "Explicacion",
                "data": {"id_siniestro": "SIN-0045"},
                "source": "tools",
                "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
                "context": {"resolved_claim_id": "SIN-0045"},
                "llm": {"status": "disabled_by_config"},
            },
            {
                "ok": True,
                "intent": "ranking_proveedores",
                "message": "Ranking",
                "data": [],
                "source": "tools",
                "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
                "context": {"resolved_claim_id": None},
                "llm": {"status": "disabled_by_config"},
            },
        ]
        with patch("api.routes.agent.answer_question", side_effect=responses):
            first = self.client.post(
                "/api/agent/chat",
                json={"user_id": "analyst-a", "message": "Explica SIN-0045"},
            ).json()["data"]
            second = self.client.post(
                "/api/agent/chat",
                json={
                    "user_id": "analyst-a",
                    "thread_id": first["thread_id"],
                    "message": "top proveedores",
                },
            ).json()["data"]

        self.assertEqual(len(second["sections"]), 2)
        self.assertTrue(all(message["section_id"] for message in second["history"]))
        self.assertEqual(second["sections"][0]["title"], "Caso SIN-0045")

    def test_agent_chat_persist_false_does_not_store_turn_or_sections(self):
        agent_response = {
            "ok": True,
            "intent": "top_riesgo",
            "message": "Respuesta temporal",
            "data": [],
            "source": "tools",
            "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
            "context": {"resolved_claim_id": None},
            "llm": {"status": "disabled_by_config"},
        }
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            response = self.client.post(
                "/api/agent/chat",
                json={"user_id": "analyst-a", "message": "top casos", "persist": False},
            )

        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["history"], [])
        self.assertEqual(payload["data"]["sections"], [])

    def test_agent_chat_can_clear_selected_claim_from_existing_thread(self):
        responses = [
            {
                "ok": True,
                "intent": "explicar_siniestro",
                "message": "Caso",
                "data": {"id_siniestro": "SIN-0045"},
                "source": "tools",
                "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
                "context": {"resolved_claim_id": "SIN-0045"},
                "llm": {"status": "disabled_by_config"},
            },
            {
                "ok": True,
                "intent": "top_riesgo",
                "message": "Portafolio",
                "data": [],
                "source": "tools",
                "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
                "context": {"resolved_claim_id": None},
                "llm": {"status": "disabled_by_config"},
            },
        ]
        with patch("api.routes.agent.answer_question", side_effect=responses):
            first = self.client.post(
                "/api/agent/chat",
                json={"user_id": "analyst-a", "message": "Explica SIN-0045", "selected_claim_id": "SIN-0045"},
            ).json()["data"]
            second = self.client.post(
                "/api/agent/chat",
                json={"user_id": "analyst-a", "thread_id": first["thread_id"], "message": "top casos", "selected_claim_id": None},
            ).json()["data"]

        self.assertIsNone(second["context"]["selected_claim_id"])

    def test_agent_thread_returns_most_recent_messages_when_history_exceeds_limit(self):
        agent_response = {
            "ok": True,
            "intent": "top_riesgo",
            "message": "Respuesta persistida",
            "data": [],
            "source": "tools",
            "runtime": {"requested": "classic", "active": "classic", "status": "ok"},
            "context": {"resolved_claim_id": None},
            "llm": {"status": "disabled_by_config"},
        }
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            first = self.client.post("/api/agent/chat", json={"user_id": "analyst-a", "message": "pregunta 0"}).json()["data"]
            thread_id = first["thread_id"]
            for index in range(1, 60):
                self.client.post(
                    "/api/agent/chat",
                    json={"user_id": "analyst-a", "thread_id": thread_id, "message": f"pregunta {index}"},
                )

        response = self.client.get(f"/api/agent/threads/{thread_id}?user_id=analyst-a")
        payload = response.json()["data"]
        self.assertEqual(len(payload["history"]), 100)
        self.assertEqual(payload["history"][0]["content"], "pregunta 10")
        self.assertEqual(payload["history"][-2]["content"], "pregunta 59")

    def test_agent_domain_error_becomes_api_error_with_details(self):
        agent_response = {"ok": False, "message": "Falta id", "hint": "Usa SIN-0045"}
        with patch("api.routes.agent.answer_question", return_value=agent_response):
            response = self.client.post("/api/agent/ask", json={"question": "explica"})

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["hint"], "Usa SIN-0045")
        self.assertEqual(payload["error"]["details"], agent_response)

    def test_report_endpoint_supports_markdown(self):
        with patch("api.routes.reports.generate_report_markdown", return_value="# Reporte") as report:
            response = self.client.get("/api/report?format=markdown&top_limit=3")

        report.assert_called_once_with(top_limit=3)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["format"], "markdown")
        self.assertEqual(payload["data"]["content"], "# Reporte")

    def test_validation_errors_use_standard_envelope(self):
        response = self.client.post("/api/agent/ask", json={"question": ""})

        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertIn("contrato", payload["error"]["message"])

    def test_savings_endpoint(self):
        savings = {"ahorro_potencial_estimado": 1000, "casos_rojos": 5}
        with patch("api.routes.reports.tools.simulate_portfolio_savings", return_value=savings):
            response = self.client.get("/api/report/savings")
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["data"]["ahorro_potencial_estimado"], 1000)

    def test_audit_endpoint_markdown(self):
        with patch("api.routes.reports.build_audit_report", return_value={"total_casos_rojos": 3}):
            with patch("api.routes.reports.render_audit_markdown", return_value="# Audit"):
                response = self.client.get("/api/report/audit?format=markdown")
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["content"], "# Audit")


if __name__ == "__main__":
    unittest.main()
