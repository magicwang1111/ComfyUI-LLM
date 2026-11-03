import asyncio
import base64
import io
import unittest
from pathlib import Path
from unittest.mock import patch

import av
import numpy as np
from PIL import Image

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
    def test_gemini_and_qwen_expose_video(self):
        self.assertEqual(nodes.GeminiLLMNode.INPUT_TYPES()["optional"]["video"], ("VIDEO",))
        self.assertEqual(nodes.QwenLLMNode.INPUT_TYPES()["optional"]["video"], ("VIDEO",))
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


class SampleVideo:
    def save_to(self, path, format, codec):
        self.saved_path = Path(path)
        with av.open(path, "w") as container:
            stream = container.add_stream("libx264", rate=2)
            stream.width, stream.height = 64, 48
            stream.pix_fmt = "yuv420p"
            for color in [(255, 0, 0)] * 2 + [(0, 255, 0)] * 2 + [(0, 0, 255)] * 2:
                pixels = np.full((48, 64, 3), color, dtype=np.uint8)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)


class QwenVideoTests(unittest.TestCase):
    def test_sampler_includes_first_middle_last_frames_and_cleans_up(self):
        video = SampleVideo()
        frames = llm.sample_qwen_video(video, 3)
        self.assertEqual([t for t, _ in frames], [0.0, 1.0, 2.5])
        for (_, data), channel in zip(frames, (0, 1, 2)):
            with Image.open(io.BytesIO(base64.b64decode(data))) as image:
                pixel = image.getpixel((32, 24))
                self.assertGreater(pixel[channel], 240)
                self.assertTrue(all(value < 10 for i, value in enumerate(pixel) if i != channel))
        self.assertFalse(video.saved_path.parent.exists())

    def test_short_video_does_not_duplicate_frames(self):
        frames = llm.sample_qwen_video(SampleVideo(), 16)
        self.assertEqual(len(frames), 6)
        self.assertEqual(len({t for t, _ in frames}), 6)
        self.assertEqual(len(llm.sample_qwen_video(SampleVideo(), 1)), 1)

    def test_invalid_video_cleans_up_and_fails_before_request(self):
        video = FakeVideo()
        with patch.object(nodes, "create_runtime_client") as client:
            with self.assertRaises(av.error.InvalidDataError):
                asyncio.run(nodes.QwenLLMNode().generate(
                    model="qwen3.8-max", user_prompt="describe", video=video,
                ))
            client.assert_not_called()

    def test_text_only_model_rejected_before_serialization(self):
        with patch.object(nodes, "sample_qwen_video") as sample:
            with self.assertRaisesRegex(ValueError, "does not support video"):
                asyncio.run(nodes.QwenLLMNode().generate(
                    model="qwen-plus-latest", user_prompt="describe", video=FakeVideo(),
                ))
            sample.assert_not_called()

    def test_video_and_reference_image_reach_qwen_with_timestamps(self):
        client = FakeClient()
        with patch.object(nodes, "create_runtime_client", return_value=client):
            text, _ = asyncio.run(nodes.QwenLLMNode().generate(
                model="qwen3.8-max", system_prompt="只描述服装变化", user_prompt="比较视频和参考图",
                video=SampleVideo(), video_frames=3,
                image=np.ones((1, 2, 2, 3), dtype=np.float32),
            ))
        provider, path, payload = client.calls[0]
        self.assertEqual((provider, path), ("qwen", "/v1/chat/completions"))
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "只描述服装变化"})
        parts = payload["messages"][1]["content"]
        self.assertEqual(parts[0]["text"], "比较视频和参考图")
        self.assertIn("不含音轨", parts[1]["text"])
        self.assertEqual([p["text"] for p in parts if p.get("text", "").startswith("视频画面：")],
                         ["视频画面：0.000 秒", "视频画面：1.000 秒", "视频画面：2.500 秒"])
        self.assertEqual(len([p for p in parts if p["type"] == "image_url"]), 4)
        self.assertIn("不属于上述视频", parts[-2]["text"])
        self.assertEqual(text, "final")
        self.assertTrue(client.closed)

    def test_default_video_prompt_and_no_video_backward_compatibility(self):
        for video in (None, SampleVideo()):
            with self.subTest(video=video):
                client = FakeClient()
                with patch.object(nodes, "create_runtime_client", return_value=client):
                    asyncio.run(nodes.QwenLLMNode().generate(
                        model="qwen3.8-max", user_prompt="describe", video=video, video_frames=2,
                    ))
                path, payload = client.calls[0][1:]
                if video is None:
                    self.assertIn("/qwen/api/", path)
                    self.assertEqual(payload["input"]["messages"][0]["content"][0]["text"], nodes.DEFAULT_SYSTEM_PROMPT)
                else:
                    self.assertIn("视频画面分析助手", payload["messages"][0]["content"])
