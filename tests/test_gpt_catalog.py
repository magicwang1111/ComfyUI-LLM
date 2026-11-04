import unittest

import numpy as np

from _loader import import_module

llm = import_module("llm")
models = import_module("models")


class GPTCatalogTests(unittest.TestCase):
    def test_all_models_build_requests_and_have_pricing(self):
        for model in models.model_names("gpt"):
            with self.subTest(model=model):
                path, payload = llm.build_request("gpt", model, "medium", "system", "hello")
                self.assertIn(path, ("/v1/chat/completions", "/v1/responses"))
                self.assertEqual(payload["model"], model)
                estimate = llm.estimate_gpt_cost(model, {"input_tokens": 300000, "output_tokens": 1000})
                self.assertGreater(estimate["estimated_cost_usd"], 0)

    def test_reasoning_limits_and_non_reasoning_models(self):
        for model, level, expected in [
            ("gpt-6.1-sol", "off", "low"), ("gpt-6-astra", "off", "low"),
            ("gpt-6.1-terra", "off", "none"), ("gpt-6-luna", "off", "none"),
            ("gpt-5", "off", "minimal"), ("gpt-5.4-pro", "low", "medium"),
            ("gpt-5-pro", "medium", "high"), ("gpt-5.3-codex", "off", "low"),
        ]:
            with self.subTest(model=model):
                payload = llm.build_gpt_payload(model, level, "", "hello")
                actual = payload.get("reasoning_effort", payload.get("reasoning", {}).get("effort"))
                self.assertEqual(actual, expected)
        for model in ("gpt-4.1", "gpt-4o", "gpt-chat-latest"):
            self.assertNotIn("reasoning_effort", llm.build_gpt_payload(model, "high", "", "hello"))
        self.assertEqual(llm.build_gpt_payload("gpt-6.1-sol", "medium", "", "hello")["max_completion_tokens"], 128000)

    def test_responses_request_preserves_image_and_instructions(self):
        path, payload = llm.build_request(
            "gpt", "gpt-5.3-codex", "medium", "Describe accurately", "What is visible?",
            np.zeros((1, 2, 2, 3), dtype=np.float32),
        )
        self.assertEqual(path, "/v1/responses")
        self.assertEqual(payload["instructions"], "Describe accurately")
        self.assertFalse(payload["store"])
        self.assertEqual(payload["input"][0]["content"][0]["text"], "What is visible?")
        self.assertTrue(payload["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,"))
        self.assertNotIn("messages", payload)

    def test_responses_extracts_only_final_text_and_rejects_incomplete(self):
        response = {"status": "completed", "output": [
            {"type": "reasoning", "summary": [{"type": "summary_text", "text": "reasoning"}]},
            {"type": "message", "content": [{"type": "output_text", "text": "answer"}]},
        ]}
        self.assertEqual(llm.extract_text("gpt", response), "answer")
        response.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        with self.assertRaisesRegex(ValueError, "incomplete"):
            llm.extract_text("gpt", response)

    def test_new_model_cost_with_cached_and_long_context_tokens(self):
        usage = {"input_tokens": 100000, "input_tokens_details": {"cached_tokens": 20000}, "output_tokens": 1000}
        self.assertAlmostEqual(llm.estimate_gpt_cost("gpt-6.1-terra", usage)["estimated_cost_usd"], 0.086)
        usage["input_tokens"] = 300000
        self.assertAlmostEqual(llm.estimate_gpt_cost("gpt-6.1-terra", usage)["estimated_cost_usd"], 0.5695)
