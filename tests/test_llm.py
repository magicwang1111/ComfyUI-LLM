import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock, patch

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
                "gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
                "gpt-5.6-sol",
                "gpt-5.6-terra",
                "gpt-5.6-luna",
                "gpt-chat-latest",
                "gpt-5.5",
                "gpt-5.4",
                "gpt-5.4-pro",
                "gpt-5.4-mini",
                "gpt-5.4-nano", "gpt-5.3-codex", "gpt-5.2", "gpt-5.2-codex",
                "gpt-5.1", "gpt-5.1-codex", "gpt-5.1-codex-mini", "gpt-5.1-codex-max",
                "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro", "gpt-5-codex",
                "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o",
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
        self.assertAlmostEqual(standard["estimated_cost_usd"], 0.0284)

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
        self.assertAlmostEqual(long_context["estimated_cost_usd"], 0.102)

    def test_gpt_cost_returns_none_without_usage(self):
        self.assertIsNone(
            llm.estimate_gpt_cost(
                "gpt-5.4-mini",
                {"choices": [{"message": {"content": "ok"}}]},
            )
        )


class QwenTests(unittest.TestCase):
    def test_all_hub_chat_models_and_vision_capabilities(self):
        expected = {
            "qwen3.8-max", "qwen3.8-flash", "qwen3.8-max-glb",
            "qwen3.7-max", "qwen3.7-plus", "qwen3.7-flash", "qwen3.7-max-glb",
            "qwen3.6-plus", "qwen3.6-flash", "qwen3.6-plus-glb", "qwen3.6-flash-glb",
            "qwen3.5-plus", "qwen3.5-flash", "qwen3.5-plus-glb", "qwen3.5-flash-glb",
            "qwen-plus-latest",
        }
        self.assertEqual(set(models.model_names("qwen")), expected)
        for model in expected:
            with self.subTest(model=model):
                payload = llm.build_qwen_payload(model, "", "hello")
                self.assertEqual(payload["model"], model)
                image = np.zeros((1, 2, 2, 3), dtype=np.float32)
                if model == "qwen-plus-latest":
                    with self.assertRaisesRegex(ValueError, "does not support image"):
                        llm.build_request("qwen", model, "medium", "", "hello", image)
                else:
                    path, payload = llm.build_request("qwen", model, "medium", "", "hello", image)
                    self.assertEqual(path, "/v1/chat/completions")
                    self.assertIn("image_url", payload["messages"][0]["content"][1])

    def test_text_and_image_requests_use_their_supported_routes(self):
        for system in ("", " system "):
            for image in (None, np.zeros((1, 2, 2, 3), dtype=np.float32)):
                with self.subTest(system=system, has_image=image is not None):
                    path, payload = llm.build_request(
                        "qwen", "qwen3.7-max", "medium", system, "中文问题", image,
                    )
                    if image is not None:
                        self.assertEqual(path, "/v1/chat/completions")
                        self.assertEqual(payload["messages"][-1]["content"][0], {"type": "text", "text": "中文问题"})
                        self.assertTrue(payload["messages"][-1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,iVBOR"))
                        self.assertFalse(payload["stream"])
                        continue
                    self.assertEqual(path, "/qwen/api/v1/services/aigc/multimodal-generation/generation")
                    self.assertEqual(payload["model"], "qwen3.7-max")
                    self.assertEqual(set(payload), {"model", "input", "parameters"})
                    self.assertEqual(payload["parameters"], {"result_format": "message"})
                    messages = payload["input"]["messages"]
                    self.assertEqual(len(messages), 2 if system else 1)
                    if system:
                        self.assertEqual(messages[0], {"role": "system", "content": [{"text": "system"}]})
                    self.assertEqual(messages[-1]["role"], "user")
                    content = messages[-1]["content"]
                    self.assertEqual(content[0], {"text": "中文问题"})
                    self.assertEqual(len(content), 1)

    def test_extract_native_string_and_block_content(self):
        for content in ("最终答案", [{"text": "最终"}, {"text": "答案"}, {"image": "ignored"}]):
            with self.subTest(content=content):
                response = {"output": {"choices": [{"message": {
                    "content": content, "reasoning_content": "hidden",
                }}]}}
                self.assertEqual(llm.extract_text("qwen", response), "最终答案")
                self.assertEqual(llm.extract_text("qwen", response["output"]), "最终答案")

    def test_empty_and_malformed_responses_fail(self):
        for response in ({}, {"output": {"choices": []}},
                         {"output": {"choices": [{"message": {"content": ""}}]}},
                         {"output": {"choices": [{"message": {"content": None}}]}}):
            with self.subTest(response=response), self.assertRaisesRegex(ValueError, "qwen response"):
                llm.extract_text("qwen", response)

    def test_native_http_request_and_api_error(self):
        async def run(status):
            async def handler(request):
                self.assertEqual(str(request.url), "https://api.vapeur.ai/qwen/api/v1/services/aigc/multimodal-generation/generation")
                self.assertEqual(request.headers["authorization"], "Bearer secret")
                self.assertIn("application/json", request.headers["content-type"])
                self.assertNotIn("x-dashscope-sse", request.headers)
                self.assertEqual(json.loads(request.content)["input"]["messages"][0]["content"], [{"text": "中文"}])
                if status == 400:
                    return httpx.Response(status, json={"code": "InvalidParameter", "message": "bad model"})
                return httpx.Response(status, json={
                    "output": {"choices": [{"message": {"content": "ok"}}]},
                    "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                    "requestId": "test-id",
                })

            client = llm.VapeurLLMClient("secret", transport=httpx.MockTransport(handler))
            try:
                path, payload = llm.build_request("qwen", "qwen3.7-max", "medium", "", "中文")
                if status == 400:
                    with self.assertRaisesRegex(llm.VapeurAPIError, "InvalidParameter.*bad model"):
                        await client.generate("qwen", path, payload)
                else:
                    response = await client.generate("qwen", path, payload)
                    self.assertEqual(llm.extract_text("qwen", response), "ok")
                    self.assertEqual(json.loads(llm.response_json(response))["usage"]["totalTokens"], 2)
            finally:
                await client.close()

        for status in (200, 400):
            with self.subTest(status=status):
                asyncio.run(run(status))


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
    def test_temporary_http_error_retries_same_request_and_recovers(self):
        async def run(status):
            seen = []

            async def handler(request):
                seen.append(request)
                if len(seen) == 1:
                    return httpx.Response(status, json={"code": 4007, "message": "", "data": None})
                return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

            client = llm.VapeurLLMClient("secret", max_retries=1, retry_delay=2, transport=httpx.MockTransport(handler))
            try:
                with patch.object(llm.asyncio, "sleep", new_callable=AsyncMock) as sleep:
                    result = await client.generate("qwen", "/v1/chat/completions", {"model": "qwen3.8-flash", "messages": []})
                    sleep.assert_awaited_once_with(2)
                self.assertEqual(llm.extract_text("qwen", result), "ok")
                self.assertEqual(len(seen), 2)
                self.assertEqual(seen[0].content, seen[1].content)
                self.assertEqual(seen[0].url, seen[1].url)
                self.assertEqual(seen[1].headers["authorization"], "Bearer secret")
            finally:
                await client.close()

        for status in (502, 503, 504):
            with self.subTest(status=status):
                asyncio.run(run(status))

    def test_http_retry_limit_and_disabled_retries(self):
        async def run(retries):
            calls = 0

            async def handler(request):
                nonlocal calls
                calls += 1
                return httpx.Response(503, json={"code": 4007, "message": "", "data": None})

            client = llm.VapeurLLMClient("secret", max_retries=retries, retry_delay=0, transport=httpx.MockTransport(handler))
            try:
                with self.assertRaises(llm.VapeurAPIError) as raised:
                    await client.generate("qwen", "/v1/chat/completions", {})
                self.assertEqual(calls, retries + 1)
                self.assertEqual(raised.exception.status_code, 503)
                self.assertIn("4007", str(raised.exception))
                self.assertIn(f"after {retries + 1} attempt(s)", str(raised.exception))
            finally:
                await client.close()

        for retries in (0, 2):
            with self.subTest(retries=retries):
                asyncio.run(run(retries))

    def test_client_errors_are_not_retried(self):
        async def run(status):
            calls = 0

            async def handler(request):
                nonlocal calls
                calls += 1
                return httpx.Response(status, json={"error": {"message": "request rejected"}})

            client = llm.VapeurLLMClient("secret", max_retries=2, retry_delay=0, transport=httpx.MockTransport(handler))
            try:
                with self.assertRaises(llm.VapeurAPIError):
                    await client.generate("qwen", "/v1/chat/completions", {})
                self.assertEqual(calls, 1)
            finally:
                await client.close()

        for status in (400, 401, 403, 429):
            with self.subTest(status=status):
                asyncio.run(run(status))

    def test_http_and_transport_errors_share_retry_budget(self):
        async def run():
            calls = 0

            async def handler(request):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return httpx.Response(503, json={"message": "unavailable"})
                if calls == 2:
                    raise httpx.ReadTimeout("timeout", request=request)
                return httpx.Response(200, json={"ok": True})

            client = llm.VapeurLLMClient("secret", max_retries=2, retry_delay=2, transport=httpx.MockTransport(handler))
            try:
                with patch.object(llm.asyncio, "sleep", new_callable=AsyncMock) as sleep:
                    self.assertEqual(await client.generate("qwen", "/v1/chat/completions", {}), {"ok": True})
                    self.assertEqual(sleep.await_count, 2)
                self.assertEqual(calls, 3)
            finally:
                await client.close()

        asyncio.run(run())

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
