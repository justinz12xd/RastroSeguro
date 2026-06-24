import unittest
from unittest.mock import Mock, patch

from src.infrastructure.llm import LLMRequest, build_llm_provider
from src.infrastructure.llm.disabled_provider import DisabledProvider
from src.infrastructure.llm.openai_provider import OpenAIProvider
from src.infrastructure.llm.settings import LLMSettings


class AgentLLMTest(unittest.TestCase):
    def test_build_provider_disabled_by_default(self):
        settings = LLMSettings(
            enabled=False,
            provider="openai",
            model="gpt-4o",
            api_key="sk-test",
            timeout_seconds=1.0,
            max_output_tokens=100,
        )

        provider = build_llm_provider(settings)

        self.assertIsInstance(provider, DisabledProvider)
        result = provider.generate(LLMRequest(intent="top_riesgo", data=[], question="top"))
        self.assertFalse(result.has_message)
        self.assertEqual(result.status, "disabled_by_config")
        self.assertEqual(result.metadata()["model"], "gpt-4o")
        self.assertFalse(result.metadata()["enabled"])

    def test_openai_provider_uses_responses_api_and_output_text(self):
        settings = LLMSettings(
            enabled=True,
            provider="openai",
            model="gpt-4o",
            api_key="sk-test",
            timeout_seconds=1.0,
            max_output_tokens=100,
        )
        response = Mock(status_code=200)
        response.json.return_value = {"output_text": "Síntesis profesional."}

        with patch("src.infrastructure.llm.openai_provider._post_json", return_value=response) as post:
            result = OpenAIProvider(settings).generate(
                LLMRequest(intent="ranking_proveedores", data=[{"id": "PROV-1"}], question="top proveedores")
            )

        self.assertTrue(result.has_message)
        self.assertEqual(result.message, "Síntesis profesional.")
        self.assertEqual(result.status, "ok")
        self.assertTrue(result.metadata()["enabled"])
        url = post.call_args.args[0]
        payload = post.call_args.kwargs["payload"]
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(url, "https://api.openai.com/v1/responses")
        self.assertEqual(payload["model"], "gpt-4o")
        self.assertIn("instructions", payload)
        self.assertIn("input", payload)
        self.assertFalse(payload["store"])
        self.assertEqual(headers["Authorization"], "Bearer sk-test")

    def test_openai_provider_falls_back_without_raising_on_http_error(self):
        settings = LLMSettings(
            enabled=True,
            provider="openai",
            model="gpt-4o",
            api_key="sk-test",
            timeout_seconds=1.0,
            max_output_tokens=100,
        )
        response = Mock(status_code=401, text="unauthorized")
        response.json.return_value = {"error": {"message": "bad key"}}

        with patch("src.infrastructure.llm.openai_provider._post_json", return_value=response):
            result = OpenAIProvider(settings).generate(LLMRequest(intent="top_riesgo", data=[], question="top"))

        self.assertFalse(result.has_message)
        self.assertEqual(result.status, "http_401")
        self.assertIn("bad key", result.error)


if __name__ == "__main__":
    unittest.main()
