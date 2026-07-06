import asyncio
import unittest
from unittest.mock import patch

from _loader import ensure_package_loaded, import_module

nodes = import_module("nodes")


class FakeClient:
    def __init__(self):
        self.calls = []
        self.closed = False

    async def generate(self, provider, path, payload):
        self.calls.append((provider, path, payload))
        if provider == "claude":
            return {"content": [{"type": "text", "text": "final"}]}
        if provider == "gemini":
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "final"}]}}
                ]
            }
        return {"choices": [{"message": {"content": "final"}}]}

    async def close(self):
        self.closed = True


class NodeTests(unittest.TestCase):
    def test_all_nodes_are_registered(self):
        package = ensure_package_loaded()
        self.assertEqual(
            set(package.NODE_CLASS_MAPPINGS),
            {
                "ComfyUI-LLM GPT",
                "ComfyUI-LLM Claude",
                "ComfyUI-LLM Gemini",
                "ComfyUI-LLM DeepSeek",
            },
        )

    def test_only_vision_nodes_have_image_input(self):
        for cls in (
            nodes.GPTLLMNode,
            nodes.ClaudeLLMNode,
            nodes.GeminiLLMNode,
        ):
            self.assertIn("image", cls.INPUT_TYPES()["optional"])
        self.assertNotIn("optional", nodes.DeepSeekLLMNode.INPUT_TYPES())

    def test_node_returns_final_text_and_json(self):
        client = FakeClient()
        with patch.object(nodes, "create_runtime_client", return_value=client):
            text, raw = asyncio.run(
                nodes.GPTLLMNode().generate(
                    model="gpt-5.5",
                    thinking_level="medium",
                    system_prompt="system",
                    user_prompt="rewrite",
                )
            )
        self.assertEqual(text, "final")
        self.assertIn('"content": "final"', raw)
        self.assertTrue(client.closed)
        self.assertEqual(client.calls[0][1], "/v1/chat/completions")


if __name__ == "__main__":
    unittest.main()

