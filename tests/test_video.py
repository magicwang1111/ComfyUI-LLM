import asyncio
import base64
import unittest
from pathlib import Path
from unittest.mock import patch

from _loader import import_module
from test_nodes import FakeClient

nodes = import_module("nodes")
llm = import_module("llm")


class FakeVideo:
    def save_to(self, path, format, codec):
        assert format == "mp4"
        assert codec == "h264"
        Path(path).write_bytes(b"video-with-audio")


class VideoTests(unittest.TestCase):
    def test_only_gemini_exposes_video(self):
        self.assertEqual(nodes.GeminiLLMNode.INPUT_TYPES()["optional"]["video"], ("VIDEO",))
        self.assertNotIn("video", nodes.GPTLLMNode.INPUT_TYPES()["optional"])

    def test_video_and_product_reach_gemini_and_return_text(self):
        client = FakeClient()
        with patch.object(nodes, "create_runtime_client", return_value=client):
            text, raw = asyncio.run(nodes.GeminiLLMNode().generate(
                model="gemini-3.5-flash", user_prompt="产品：纯棉T恤，写30秒口播",
                video=FakeVideo(),
            ))
        provider, path, payload = client.calls[0]
        self.assertEqual(provider, "gemini")
        parts = payload["contents"][0]["parts"]
        self.assertIn("纯棉T恤", parts[0]["text"])
        self.assertEqual(parts[-1]["inlineData"]["mimeType"], "video/mp4")
        self.assertEqual(base64.b64decode(parts[-1]["inlineData"]["data"]), b"video-with-audio")
        self.assertIn("产品资料", payload["systemInstruction"]["parts"][0]["text"])
        self.assertEqual(text, "final")
        self.assertTrue(client.closed)

    def test_custom_system_prompt_is_preserved(self):
        client = FakeClient()
        with patch.object(nodes, "create_runtime_client", return_value=client):
            asyncio.run(nodes.GeminiLLMNode().generate(
                model="gemini-3.5-flash", system_prompt="只转写原口播",
                user_prompt="转写", video=FakeVideo(),
            ))
        self.assertEqual(client.calls[0][2]["systemInstruction"]["parts"][0]["text"], "只转写原口播")

    def test_oversize_video_fails_before_api_request(self):
        with patch.object(llm, "MAX_INLINE_VIDEO_BYTES", 3):
            with self.assertRaisesRegex(ValueError, "too large"):
                llm.encode_video(FakeVideo())

    def test_empty_video_fails(self):
        class EmptyVideo:
            def save_to(self, path, format, codec):
                Path(path).write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "empty"):
            llm.encode_video(EmptyVideo())
