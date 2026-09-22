import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx
import numpy as np

from _loader import import_module

llm = import_module("llm")
models = import_module("models")


class PayloadTests(unittest.TestCase):
    def test_fixed_model_lists_and_defaults(self):
        self.assertEqual(
            models.model_names("gpt"),
            [
                "gpt-5.6-sol",
                "gpt-5.6-terra",
                "gpt-5.6-luna",
                "gpt-5.5",
                "gpt-5.4",
                "gpt-5.4-mini",
            ],
        )
        self.assertEqual(models.default_model("gpt"), "gpt-5.5")
        self.assertEqual(models.default_model("claude"), "claude-sonnet-5")
        self.assertEqual(
            models.model_names("gemini"),
            [
                "gemini-3.8-flash",
                "gemini-3.7-flash",
                "gemini-3.6-flash",
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite",
                "gemini-3.1-pro-preview",
                "gemini-3.1-flash-lite",
                "gemini-3-flash-preview",
                "gemini-2.5-flash",
            ],
        )
        self.assertEqual(models.default_model("gemini"), "gemini-3.5-flash")
        self.assertEqual(models.default_model("deepseek"), "deepseek-v4-flash-cn")

    def test_gpt_payload_uses_chat_vision_and_max_output(self):
        payload = llm.build_gpt_payload(
            "gpt-5.6-sol", "high", "system", "rewrite", "abc"
        )
        self.assertEqual(payload["max_completion_tokens"], 128000)
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertEqual(
            payload["messages"][1]["content"][1]["image_url"]["url"],
            "data:image/png;base64,abc",
        )

    def test_deepseek_off_disables_thinking(self):
        payload = llm.build_deepseek_payload(
            "deepseek-v4-flash-cn", "off", "", "rewrite"
        )
        self.assertEqual(payload["max_tokens"], 131072)
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertNotIn("reasoning_effort", payload)

    def test_claude_adaptive_and_manual_thinking(self):
        opus = llm.build_claude_payload(
            "claude-opus-4-8", "medium", "system", "rewrite"
        )
        self.assertEqual(opus["thinking"], {"type": "adaptive"})
        self.assertEqual(opus["output_config"], {"effort": "medium"})

        haiku = llm.build_claude_payload(
            "claude-haiku-4-5", "high", "system", "rewrite"
        )
        self.assertEqual(
            haiku["thinking"],
            {"type": "enabled", "budget_tokens": 32768},
        )
        self.assertEqual(haiku["max_tokens"], 64000)

    def test_claude_image_uses_base64_source(self):
        payload = llm.build_claude_payload(
            "claude-sonnet-5", "off", "system", "rewrite", "abc"
        )
        image = payload["messages"][0]["content"][0]
        self.assertEqual(image["type"], "image")
        self.assertEqual(image["source"]["data"], "abc")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertNotIn("system", payload)
        text = payload["messages"][0]["content"][1]["text"]
        self.assertIn("<system_instructions>\nsystem", text)
        self.assertIn("<user_request>\nrewrite", text)

    def test_gemini3_thinking_off_maps_to_supported_minimum(self):
        minimums = {
            "gemini-3.8-flash": "low",
            "gemini-3.7-flash": "low",
            "gemini-3.6-flash": "minimal",
            "gemini-3.5-flash": "minimal",
            "gemini-3.5-flash-lite": "minimal",
            "gemini-3.1-pro-preview": "low",
            "gemini-3.1-flash-lite": "minimal",
            "gemini-3-flash-preview": "minimal",
        }
        for model, minimum in minimums.items():
            with self.subTest(model=model):
                payload = llm.build_gemini_payload(model, "off", "", "rewrite")
                self.assertEqual(
                    payload["generationConfig"]["thinkingConfig"],
                    {"thinkingLevel": minimum},
                )

    def test_gemini3_thinking_levels_are_preserved(self):
        for model in models.model_names("gemini"):
            if model == "gemini-2.5-flash":
                continue
            for level in ("low", "medium", "high"):
                with self.subTest(model=model, level=level):
                    payload = llm.build_gemini_payload(model, level, "", "rewrite")
                    self.assertEqual(
                        payload["generationConfig"]["thinkingConfig"],
                        {"thinkingLevel": level},
                    )

    def test_gemini25_flash_uses_thinking_budgets_and_off_disables_thinking(self):
        budgets = {"off": 0, "low": 1024, "medium": 8192, "high": 24576}
        for level, budget in budgets.items():
            with self.subTest(level=level):
                _, payload = llm.build_request(
                    "gemini", "gemini-2.5-flash", level, "system", "rewrite"
                )
                self.assertEqual(
                    payload["generationConfig"]["thinkingConfig"],
                    {"thinkingBudget": budget},
                )

    def test_gemini_requests_use_provider_output_limit_and_default_thinking(self):
        for model in models.model_names("gemini"):
            with self.subTest(model=model):
                path, payload = llm.build_request(
                    "gemini", model, models.DEFAULT_THINKING_LEVEL, "", "rewrite"
                )
                self.assertEqual(path, f"/gemini/v1beta/models/{model}:generateContent")
                self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 65536)
                self.assertEqual(
                    payload["generationConfig"]["thinkingConfig"],
                    {"thinkingBudget": 8192}
                    if model == "gemini-2.5-flash"
                    else {"thinkingLevel": "medium"},
                )

    def test_single_image_encoding_rejects_batches(self):
        with self.assertRaisesRegex(ValueError, "Exactly one image"):
            llm.encode_single_image(np.zeros((2, 4, 4, 3), dtype=np.float32))
        encoded = llm.encode_single_image(
            np.zeros((1, 4, 4, 3), dtype=np.float32)
        )
        self.assertTrue(encoded.startswith("iVBOR"))

    def test_response_extractors_exclude_thinking(self):
        self.assertEqual(
            llm.extract_text(
                "deepseek",
                {
                    "choices": [
                        {
                            "message": {
                                "reasoning_content": "private",
                                "content": "final",
                            }
                        }
                    ]
                },
            ),
            "final",
        )
        self.assertEqual(
            llm.extract_text(
                "gemini",
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": "thought", "thought": True},
                                    {"text": "final"},
                                ]
                            }
                        }
                    ]
                },
            ),
            "final",
        )

    def test_gpt_cost_uses_cached_tokens_and_long_context_tier(self):
        standard = llm.estimate_gpt_cost(
            "gpt-5.6-luna",
            {
                "usage": {
                    "prompt_tokens": 100_000,
                    "completion_tokens": 10_000,
                    "prompt_tokens_details": {"cached_tokens": 20_000},
                }
            },
        )
        self.assertEqual(standard["context_tier"], "standard")
        self.assertAlmostEqual(standard["estimated_cost_usd"], 0.142)

        long_context = llm.estimate_gpt_cost(
            "gpt-5.6-luna",
            {
                "usage": {
                    "input_tokens": 300_000,
                    "output_tokens": 10_000,
                    "input_tokens_details": {"cached_tokens": 100_000},
                }
            },
        )
        self.assertEqual(long_context["context_tier"], "long_context")
        self.assertAlmostEqual(long_context["estimated_cost_usd"], 0.51)

    def test_gpt_cost_returns_none_without_usage(self):
        self.assertIsNone(
            llm.estimate_gpt_cost(
                "gpt-5.4-mini",
                {"choices": [{"message": {"content": "ok"}}]},
            )
        )


class ConfigTests(unittest.TestCase):
    def test_vapeur_specific_key_wins_over_legacy_key(self):
        with patch.object(
            llm,
            "load_config",
            return_value={
                "VAPEUR_API_KEY": "vapeur-key",
                "api_provider": "vapeur",
                "api_key": "legacy-key",
            },
        ):
            with patch.dict(os.environ, {"VAPEUR_API_KEY": "env-key"}):
                self.assertEqual(
                    llm.resolve_runtime_config()["api_key"],
                    "vapeur-key",
                )

    def test_missing_key_raises(self):
        with patch.object(llm, "load_config", return_value={}):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "VAPEUR_API_KEY"):
                    llm.resolve_runtime_config()


class TransportTests(unittest.TestCase):
    def test_provider_auth_headers_and_routes(self):
        seen = []

        async def handler(request):
            seen.append(request)
            if "/claude/" in request.url.path:
                body = {"content": [{"type": "text", "text": "ok"}]}
            elif "/gemini/" in request.url.path:
                body = {
                    "candidates": [
                        {"content": {"parts": [{"text": "ok"}]}}
                    ]
                }
            else:
                body = {"choices": [{"message": {"content": "ok"}}]}
            return httpx.Response(200, json=body)

        async def run():
            client = llm.VapeurLLMClient(
                "secret",
                transport=httpx.MockTransport(handler),
            )
            try:
                await client.generate(
                    "gpt",
                    "/v1/chat/completions",
                    {"messages": [{"content": "中文"}]},
                )
                await client.generate("claude", "/claude/v1/messages", {})
                await client.generate(
                    "gemini",
                    "/gemini/v1beta/models/test:generateContent",
                    {},
                )
            finally:
                await client.close()

        asyncio.run(run())
        self.assertEqual(seen[0].headers["authorization"], "Bearer secret")
        self.assertEqual(seen[1].headers["x-api-key"], "secret")
        self.assertEqual(seen[2].headers["x-goog-api-key"], "secret")
        self.assertIn("charset=utf-8", seen[0].headers["content-type"])
        self.assertIn("中文", seen[0].content.decode("utf-8"))
        self.assertNotIn("??", seen[0].content.decode("utf-8"))

    def test_http_error_is_sanitized(self):
        async def handler(request):
            return httpx.Response(
                401,
                json={"error": {"message": "bad key"}},
            )

        async def run():
            client = llm.VapeurLLMClient(
                "secret",
                transport=httpx.MockTransport(handler),
            )
            try:
                with self.assertRaisesRegex(llm.VapeurAPIError, "bad key"):
                    await client.generate("gpt", "/v1/chat/completions", {})
            finally:
                await client.close()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
