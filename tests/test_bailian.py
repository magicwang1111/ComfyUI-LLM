import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from _loader import import_module

nodes = import_module("nodes")
bailian = import_module("bailian")
models = import_module("models")


def sse(*chunks):
    body = "".join(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n" for chunk in chunks)
    return (body + "data: [DONE]\n\n").encode("utf-8")


STREAM = sse(
    {"id": "c1", "model": "qwen3.8-omni-flash", "choices": [{"delta": {"reasoning_content": "想"}, "finish_reason": None}]},
    {"id": "c1", "choices": [{"delta": {"content": "新口"}, "finish_reason": None}]},
    {"id": "c1", "choices": [{"delta": {"content": "播"}, "finish_reason": "stop"}]},
    {"id": "c1", "choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 3}},
)


class FakeVideo:
    def __init__(self, size=16):
        self.size = size

    def save_to(self, path, format, codec):
        assert (format, codec) == ("mp4", "h264")
        Path(path).write_bytes(b"v" * self.size)


def make_client(handler):
    return bailian.BailianClient(
        "sk-test", base_url="https://ws-test.cn-beijing.maas.aliyuncs.com",
        max_retries=1, retry_delay=0, transport=httpx.MockTransport(handler),
    )


class BailianTests(unittest.TestCase):
    def test_node_contract(self):
        inputs = nodes.BailianQwenNode.INPUT_TYPES()
        self.assertEqual(list(inputs["required"]), ["model", "thinking_level", "system_prompt", "user_prompt"])
        self.assertEqual(inputs["required"]["model"][1]["default"], "qwen3.8-omni-flash")
        self.assertEqual(inputs["optional"], {"image": ("IMAGE",), "video": ("VIDEO",)})

    def test_thinking_mapping(self):
        self.assertEqual(bailian.thinking_params("qwen3.8-omni-flash", "off"), {"reasoning_effort": "low"})
        self.assertEqual(bailian.thinking_params("qwen3.8-omni-flash", "high"), {"reasoning_effort": "xhigh"})
        self.assertEqual(bailian.thinking_params("qwen3.8-max", "off"), {"reasoning_effort": "none"})
        self.assertEqual(bailian.thinking_params("qwen3.7-plus", "off"), {"enable_thinking": False})
        self.assertEqual(bailian.thinking_params("qwen3.7-plus", "low"), {"enable_thinking": True, "thinking_budget": 4096})
        self.assertEqual(bailian.thinking_params("qwen3.7-plus", "high"), {"enable_thinking": True})
        self.assertEqual(bailian.thinking_params("qwen3.5-omni-flash", "high"), {})

    def test_payload_streams_and_puts_video_first(self):
        payload = bailian.build_bailian_payload("qwen3.5-omni-flash", "low", "sys", "写口播", video_url="data:;base64,AA")
        self.assertTrue(payload["stream"])
        self.assertEqual(payload["modalities"], ["text"])
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "sys"})
        content = payload["messages"][1]["content"]
        self.assertEqual(content[0], {"type": "video_url", "video_url": {"url": "data:;base64,AA"}})
        self.assertEqual(content[-1], {"type": "text", "text": "写口播"})

    def test_stream_aggregation_and_text_only_request(self):
        seen = {}

        def handler(request):
            seen["url"] = str(request.url)
            seen["headers"] = request.headers
            seen["body"] = json.loads(request.content)
            return httpx.Response(200, content=STREAM)

        client = make_client(handler)
        payload = bailian.build_bailian_payload("qwen3.8-omni-flash", "medium", "", "hi")
        response = asyncio.run(client.chat(payload))
        asyncio.run(client.close())
        self.assertEqual(seen["url"], "https://ws-test.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.assertNotIn("x-dashscope-ossresourceresolve", seen["headers"])
        self.assertEqual(seen["body"]["messages"], [{"role": "user", "content": "hi"}])
        self.assertEqual(bailian.extract_bailian_text(response), "新口播")
        self.assertEqual(response["choices"][0]["message"]["reasoning_content"], "想")
        self.assertEqual(response["usage"]["completion_tokens"], 3)

    def test_large_video_uses_temporary_upload(self):
        calls = []

        def handler(request):
            calls.append(request)
            if request.url.path == "/api/v1/uploads":
                self.assertEqual(request.url.params["model"], "qwen3.8-omni-flash")
                return httpx.Response(200, json={"data": {
                    "upload_dir": "dashscope-instant/x", "upload_host": "https://oss.example.com",
                    "oss_access_key_id": "id", "signature": "sig", "policy": "pol",
                    "x_oss_object_acl": "private", "x_oss_forbid_overwrite": "true",
                }})
            if request.url.host == "oss.example.com":
                return httpx.Response(200)
            body = json.loads(request.content)
            url = body["messages"][-1]["content"][0]["video_url"]["url"]
            self.assertTrue(url.startswith("oss://dashscope-instant/x/"))
            self.assertEqual(request.headers["X-DashScope-OssResourceResolve"], "enable")
            return httpx.Response(200, content=STREAM)

        client = make_client(handler)
        with patch.object(bailian, "MAX_BASE64_VIDEO_CHARS", 8), \
                patch.object(bailian, "create_bailian_client", return_value=client):
            text, _ = asyncio.run(nodes.BailianQwenNode().generate(
                model="qwen3.8-omni-flash", user_prompt="产品资料", video=FakeVideo(),
            ))
        self.assertEqual(text, "新口播")
        self.assertEqual(len(calls), 3)

    def test_small_video_inline_with_video_prompt(self):
        seen = {}

        def handler(request):
            seen["body"] = json.loads(request.content)
            return httpx.Response(200, content=STREAM)

        with patch.object(bailian, "create_bailian_client", return_value=make_client(handler)):
            asyncio.run(nodes.BailianQwenNode().generate(
                model="qwen3.8-omni-flash", user_prompt="产品资料", video=FakeVideo(),
            ))
        messages = seen["body"]["messages"]
        self.assertEqual(messages[0]["content"], models.VIDEO_SYSTEM_PROMPT)
        self.assertEqual(messages[1]["content"][0]["video_url"]["url"], "data:;base64,dnZ2dnZ2dnZ2dnZ2dnZ2dg==")

    def test_retries_502_then_reports_400(self):
        statuses = iter([502, 400])

        def handler(request):
            return httpx.Response(next(statuses), json={"error": {"code": "InvalidParameter", "message": "bad"}})

        client = make_client(handler)
        with self.assertRaises(bailian.BailianAPIError) as ctx:
            asyncio.run(client.chat(bailian.build_bailian_payload("qwen3.8-flash", "off", "", "hi")))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("InvalidParameter", str(ctx.exception))

    def _asr_handler(self, calls, final_status="SUCCEEDED", transcription=None):
        polls = iter(["RUNNING", final_status])

        def handler(request):
            calls.append(request)
            path = request.url.path
            if path == "/api/v1/uploads":
                self.assertEqual(request.url.params["model"], bailian.ASR_MODEL)
                return httpx.Response(200, json={"data": {
                    "upload_dir": "dashscope-instant/a", "upload_host": "https://oss.example.com",
                    "oss_access_key_id": "id", "signature": "sig", "policy": "pol",
                    "x_oss_object_acl": "private", "x_oss_forbid_overwrite": "true",
                }})
            if request.url.host == "oss.example.com":
                return httpx.Response(200)
            if path == bailian.ASR_SUBMIT_PATH:
                self.assertEqual(request.headers["X-DashScope-Async"], "enable")
                self.assertEqual(request.headers["X-DashScope-OssResourceResolve"], "enable")
                body = json.loads(request.content)
                self.assertEqual(body["model"], "qwen-audio-3.1-asr-flash-filetrans")
                self.assertTrue(body["input"]["file_urls"][0].startswith("oss://dashscope-instant/a/"))
                self.assertEqual(body["parameters"], {"language_hints": ["zh"]})
                return httpx.Response(200, json={"output": {"task_id": "t1", "task_status": "PENDING"}})
            if path == "/api/v1/tasks/t1":
                status = next(polls)
                result = {"subtask_status": status, "transcription_url": "https://result.example.com/r.json"}
                if status == "FAILED":
                    result.update(code="InvalidFile.NoAudio", message="no audio")
                return httpx.Response(200, json={"output": {"task_status": status, "results": [result]}})
            if request.url.host == "result.example.com":
                return httpx.Response(200, json=transcription)
            raise AssertionError(f"unexpected {request.url}")

        return handler

    def test_asr_node_transcribes_with_timestamps(self):
        calls = []
        transcription = {"transcripts": [{"text": "姐妹们，绝了。129元两条。", "sentences": [
            {"begin_time": 240, "end_time": 3970, "text": "姐妹们，绝了。"},
            {"begin_time": 64500, "end_time": 67920, "text": "129元两条。"},
        ]}]}
        client = make_client(self._asr_handler(calls, transcription=transcription))
        with patch.object(bailian, "create_bailian_client", return_value=client), \
                patch.object(bailian, "ASR_POLL_INTERVAL", 0):
            text, raw = asyncio.run(nodes.BailianASRNode().transcribe(FakeVideo(), "zh", True, False))
        self.assertEqual(text, "[00:00.24-00:03.97] 姐妹们，绝了。\n[01:04.50-01:07.92] 129元两条。")
        self.assertEqual(json.loads(raw)["transcription"], transcription)
        self.assertEqual(len(calls), 6)

        client = make_client(self._asr_handler([], transcription=transcription))
        with patch.object(bailian, "create_bailian_client", return_value=client), \
                patch.object(bailian, "ASR_POLL_INTERVAL", 0):
            text, _ = asyncio.run(nodes.BailianASRNode().transcribe(FakeVideo(), "zh", False, False))
        self.assertEqual(text, "姐妹们，绝了。129元两条。")

    def test_asr_no_speech_and_failure(self):
        self.assertEqual(bailian.format_transcript({"transcripts": []}), bailian.NO_SPEECH_TEXT)
        client = make_client(self._asr_handler([], final_status="FAILED"))
        with patch.object(bailian, "create_bailian_client", return_value=client), \
                patch.object(bailian, "ASR_POLL_INTERVAL", 0):
            with self.assertRaises(ValueError) as ctx:
                asyncio.run(nodes.BailianASRNode().transcribe(FakeVideo(), "zh"))
        self.assertIn("InvalidFile.NoAudio", str(ctx.exception))

    def test_config_strips_api_suffix(self):
        with patch.object(bailian, "load_config", return_value={
            "BAILIAN_API_KEY": "sk", "BAILIAN_BASE_URL": "ws-1.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/",
        }):
            config = bailian.resolve_bailian_config()
        self.assertEqual(config["base_url"], "https://ws-1.cn-beijing.maas.aliyuncs.com")

    def test_missing_key(self):
        with patch.object(bailian, "load_config", return_value={}), patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                bailian.resolve_bailian_config()


if __name__ == "__main__":
    unittest.main()
