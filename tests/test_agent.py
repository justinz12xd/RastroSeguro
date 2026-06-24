import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from src.agent.antifraud_agent import answer_question, get_quick_questions
from src.agent.entities import extract_claim_id, extract_limit
from src.agent.router import route, route_intent


class AgentTest(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict("os.environ", {"RASTRO_LLM_ENABLED": "false"}, clear=False)
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_router_detects_key_intents(self):
        self.assertEqual(route_intent("Que proveedores concentran alertas?"), "ranking_proveedores")
        self.assertEqual(route_intent("Explicame SIN-0045"), "explicar_siniestro")
        self.assertEqual(route_intent("Que narrativas similares tiene SIN-0045?"), "narrativas_similares")
        self.assertEqual(route_intent("Que conexiones de grafo tiene SIN-0045?"), "conexiones_grafo")
        self.assertEqual(route_intent("Que proveedores concentran el 80% de las alertas rojas?"), "concentracion_rojos")
        self.assertEqual(route_intent("Estima el ahorro potencial del portafolio"), "ahorro_potencial")
        self.assertEqual(route_intent("Hay redes de fraude organizadas?"), "redes_fraude")
        self.assertEqual(route_intent("Que dia es hoy?"), "fecha_actual")
        self.assertEqual(route_intent("Hola"), "saludo")
        self.assertEqual(route_intent("Que puedes hacer?"), "ayuda_agente")
        self.assertTrue(route("Que reglas usan para el score").uses_documentation)

    def test_entity_extraction(self):
        self.assertEqual(extract_claim_id("explica sin_0045"), "SIN-0045")
        self.assertEqual(extract_limit("top 15 casos"), 15)
        self.assertEqual(extract_limit("top 999 casos"), 50)

    def test_missing_claim_id_returns_helpful_error(self):
        response = answer_question("Explicame este siniestro")

        self.assertFalse(response["ok"])
        self.assertEqual(response["intent"], "explicar_siniestro")
        self.assertIn("SIN-0045", response["hint"])

    def test_follow_up_recovers_claim_id_from_history(self):
        history = [
            {"role": "user", "content": "Explicame el siniestro SIN-0045"},
            {"role": "assistant", "content": "El siniestro fue marcado en alto riesgo."},
        ]
        with patch("src.application.risk_queries.explain_claim", return_value={"id_siniestro": "SIN-0045"}) as tool:
            response = answer_question("Y por que tiene ese score?", history=history)

        tool.assert_called_once_with("SIN-0045")
        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "explicar_siniestro")

    def test_follow_up_without_claim_id_in_history_still_errors(self):
        history = [{"role": "user", "content": "Dame el top de proveedores"}]
        response = answer_question("Explicame ese siniestro", history=history)

        self.assertFalse(response["ok"])
        self.assertEqual(response["intent"], "explicar_siniestro")
        self.assertIn("SIN-0045", response["hint"])

    def test_selected_claim_id_can_resume_without_repeating_the_id(self):
        with patch("src.application.risk_queries.explain_claim", return_value={"id_siniestro": "SIN-7777"}) as tool:
            response = answer_question("Explicamelo", selected_claim_id="SIN-7777")

        tool.assert_called_once_with("SIN-7777")
        self.assertTrue(response["ok"])
        self.assertEqual(response["context"]["resolved_claim_id"], "SIN-7777")

    def test_langgraph_respects_contextual_claim_intent(self):
        with patch("src.application.risk_queries.explain_claim", return_value={"id_siniestro": "SIN-7777"}) as explain, patch(
            "src.application.risk_queries.get_top_risky_claims",
            return_value=[{"id_siniestro": "SIN-OTHER"}],
        ) as top:
            response = answer_question("que paso aqui?", selected_claim_id="SIN-7777")

        explain.assert_called_once_with("SIN-7777")
        top.assert_not_called()
        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "explicar_siniestro")
        self.assertEqual(response["runtime"]["active"], "langgraph")
        self.assertIn("Investigador de caso", response["runtime"]["agents"])

    def test_date_question_with_selected_claim_does_not_explain_claim(self):
        fixed_now = datetime(2026, 5, 29, 10, 0, tzinfo=timezone(timedelta(hours=-5), "America/Guayaquil"))
        with patch("src.agent.antifraud_agent._now_in_timezone", return_value=fixed_now), patch(
            "src.application.risk_queries.explain_claim",
            return_value={"id_siniestro": "SIN-000678"},
        ) as explain, patch(
            "src.application.risk_queries.get_top_risky_claims",
            return_value=[{"id_siniestro": "SIN-OTHER"}],
        ) as top:
            response = answer_question("que dia es hoy", selected_claim_id="SIN-000678")

        explain.assert_not_called()
        top.assert_not_called()
        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "fecha_actual")
        self.assertEqual(response["source"], "agent")
        self.assertIn("viernes, 29 de mayo de 2026", response["message"])
        self.assertEqual(response["llm"]["status"], "bypassed_for_direct_intent")
        self.assertIn("Asistente general", response["runtime"]["agents"])

    def test_missing_scored_file_returns_actionable_error(self):
        with patch(
            "src.application.risk_queries._load_scored",
            side_effect=FileNotFoundError(
                "No se encontro data/processed/siniestros_scored.csv. Ejecuta python -m src.scoring.final_score"
            ),
        ):
            response = answer_question("top 10 casos de mayor riesgo")

        self.assertFalse(response["ok"])
        self.assertEqual(response["intent"], "top_riesgo")
        self.assertIn("data/processed/siniestros_scored.csv", response["hint"])

    def test_agent_routes_pdf_questions(self):
        fake_df = __import__("pandas").DataFrame(
            [
                {
                    "id_siniestro": "SIN-0001",
                    "id_asegurado": "ASEG-1",
                    "id_proveedor": "PROV-1",
                    "ramo": "vehiculos",
                    "ciudad": "Quito",
                    "monto_reclamado": 9000,
                    "suma_asegurada": 10000,
                    "score_final": 90,
                    "nivel_riesgo": "Rojo",
                    "documentos_completos": "No",
                    "dias_desde_inicio_poliza": 5,
                    "accion_sugerida": "Revisar",
                }
            ]
        )
        with patch("src.application.risk_queries._load_scored", return_value=fake_df):
            response = answer_question("Que asegurados tienen mayor frecuencia de reclamos?")
        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "frecuencia_asegurados")

    def test_agent_routes_fraud_rings_intent(self):
        rings_payload = {"total_anillos": 1, "anillos": [], "explicacion_global": "ok"}
        with patch("src.application.risk_queries.get_fraud_rings", return_value=rings_payload) as tool:
            response = answer_question("Hay redes de fraude organizadas en el portafolio?")

        tool.assert_called_once_with(limit=10)
        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "redes_fraude")
        self.assertEqual(response["data"], rings_payload)

    def test_agent_wraps_tool_success(self):
        with patch("src.application.risk_queries.get_provider_risk_ranking", return_value=[{"id_proveedor": "PROV-1"}]) as tool:
            response = answer_question("top 3 proveedores")

        tool.assert_called_once_with(limit=3)
        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "ranking_proveedores")
        self.assertEqual(response["source"], "tools")
        self.assertEqual(response["data"], [{"id_proveedor": "PROV-1"}])
        self.assertEqual(response["llm"]["status"], "disabled_by_config")
        self.assertEqual(response["llm"]["model"], "gpt-4o")
        self.assertEqual(response["runtime"]["active"], "langgraph")

    def test_multiagent_runtime_is_default_and_traces_specialists(self):
        with patch("src.application.risk_queries.get_provider_risk_ranking", return_value=[{"id_proveedor": "PROV-1"}]):
            response = answer_question("top 3 proveedores")

        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "ranking_proveedores")
        self.assertEqual(response["data"], [{"id_proveedor": "PROV-1"}])
        self.assertEqual(response["runtime"]["active"], "langgraph")
        self.assertEqual(response["runtime"]["topology"], "supervisor-workers")
        agents = response["runtime"]["agents"]
        self.assertIn("Supervisor", agents)
        self.assertIn("Analista de portafolio", agents)
        self.assertIn("Sintetizador", agents)

    def test_langgraph_runtime_falls_back_cleanly_when_dependency_is_missing(self):
        from src.agent.langgraph_runtime import LangGraphUnavailableError

        with patch("src.application.risk_queries.get_provider_risk_ranking", return_value=[{"id_proveedor": "PROV-1"}]), patch(
            "src.agent.antifraud_agent.run_langgraph_turn",
            side_effect=LangGraphUnavailableError("missing"),
        ):
            response = answer_question("top 3 proveedores", runtime="langgraph")

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"], [{"id_proveedor": "PROV-1"}])
        self.assertEqual(response["runtime"]["requested"], "langgraph")
        self.assertEqual(response["runtime"]["active"], "classic")
        self.assertEqual(response["runtime"]["status"], "langgraph_not_installed")

    def test_agent_uses_llm_message_when_provider_returns_text(self):
        class FakeProvider:
            def generate(self, request):
                from src.infrastructure.llm import LLMResult

                return LLMResult(
                    message="Respuesta ejecutiva generada con evidencia verificada.",
                    provider="openai",
                    model="test-model",
                    status="ok",
                    enabled=True,
                )

        with patch("src.application.risk_queries.get_provider_risk_ranking", return_value=[{"id_proveedor": "PROV-1"}]), \
             patch("src.agent.antifraud_agent.build_llm_provider", return_value=FakeProvider()):
            response = answer_question("top 3 proveedores")

        self.assertTrue(response["ok"])
        self.assertEqual(response["source"], "llm")
        self.assertIn("Respuesta ejecutiva", response["message"])
        self.assertEqual(response["data"], [{"id_proveedor": "PROV-1"}])
        self.assertEqual(response["llm"]["provider"], "openai")
        self.assertEqual(response["llm"]["status"], "ok")
        self.assertTrue(response["llm"]["enabled"])

    def test_documentation_intent_uses_rag_source(self):
        response = answer_question("Que reglas se usan para calcular el score?")

        self.assertTrue(response["ok"])
        self.assertEqual(response["intent"], "documentacion")
        self.assertEqual(response["source"], "rag")
        self.assertIsInstance(response["data"], list)

    def test_rag_advanced_relevance_and_chunking(self):
        from src.agent.rag import search_docs

        results = search_docs("score final compuesto")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        for match in results:
            self.assertIn("source", match)
            self.assertIn("snippet", match)
            self.assertLess(len(match["snippet"]), 1000)

        top_snippet = results[0]["snippet"].lower()
        self.assertTrue(any(word in top_snippet for word in ["score", "final", "compuesto"]))

    def test_quick_questions_are_available_for_ui(self):
        fake_df = __import__("pandas").DataFrame(
            [
                {
                    "id_siniestro": "SIN-000088",
                    "id_asegurado": "ASEG-1",
                    "id_proveedor": "PROV-1",
                    "ramo": "vehiculos",
                    "ciudad": "Quito",
                    "monto_reclamado": 9000,
                    "suma_asegurada": 10000,
                    "score_final": 99.0,
                    "nivel_riesgo": "Rojo",
                    "accion_sugerida": "Revisar",
                }
            ]
        )
        with patch("src.application.risk_queries._load_scored", return_value=fake_df):
            questions = get_quick_questions()

        self.assertGreaterEqual(len(questions), 5)
        self.assertTrue(any("proveedores" in question.lower() for question in questions))
        self.assertTrue(any("SIN-000088" in question for question in questions))


if __name__ == "__main__":
    unittest.main()
