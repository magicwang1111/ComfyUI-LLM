import asyncio
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

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


class FakeAgentWorkerClient:
    def __init__(self, *args, **kwargs):
        pass

    async def run(self, job, work_dir, on_event=None):
        artifact_store = import_module("artifact_store")
        store = artifact_store.LocalArtifactStore(
            job["output_root"],
            job_id=job["job_id"],
            job_dir=job["job_dir"],
        )
        if on_event:
            on_event({"event": "status", "message": "test progress"})
        path = store.output_path("result.png")
        Image.new("RGB", (8, 6), "red").save(path)
        record = store.add(path, width=8, height=6)
        return {
            "status": "completed",
            "route": {
                "skill_name": "fashion-design-analysis",
                "mode": "auto",
                "confidence": 0.95,
                "input_roles": [],
                "missing_inputs": [],
                "reason": "test",
                "needs_input": False,
            },
            "text": "完成",
            "events": [{"event": "test"}],
            "artifacts": [record.disk_dict()],
        }


class FakeTextAgentWorkerClient:
    def __init__(self, *args, **kwargs):
        pass

    async def run(self, job, work_dir, on_event=None):
        return {
            "status": "completed",
            "route": {
                "skill_name": "world-buyer",
                "mode": "text-only",
                "confidence": 1.0,
                "input_roles": [],
                "missing_inputs": [],
                "reason": "explicit text-only request",
                "needs_input": False,
            },
            "text": "纯文字买手分析",
            "events": [{"event": "agent_completed"}],
            "artifacts": [],
        }


class NodeTests(unittest.TestCase):
    def test_progress_events_are_sent_and_sensitive_details_are_filtered(self):
        sent = []
        prompt_server = SimpleNamespace(
            instance=SimpleNamespace(send_sync=lambda name, payload: sent.append((name, payload)))
        )
        terminal = io.StringIO()
        with (
            patch.dict(sys.modules, {"server": SimpleNamespace(PromptServer=prompt_server)}),
            redirect_stdout(terminal),
        ):
            nodes._send_agent_progress(
                42,
                {
                    "event": "tool_start",
                    "message": "正在生成",
                    "tool": "generate_image",
                    "path": "D:/secret/file.png",
                },
            )
        self.assertEqual(sent[0][0], nodes.AGENT_PROGRESS_EVENT)
        self.assertEqual(sent[0][1]["node_id"], "42")
        self.assertNotIn("path", sent[0][1])
        self.assertIn("[ComfyUI-LLM Agent][tool_start] 正在生成", terminal.getvalue())
        self.assertNotIn("D:/secret", terminal.getvalue())

    def test_all_nodes_are_registered(self):
        package = ensure_package_loaded()
        self.assertEqual(
            set(package.NODE_CLASS_MAPPINGS),
            {
                "ComfyUI-LLM GPT",
                "ComfyUI-LLM Claude",
                "ComfyUI-LLM Gemini",
                "ComfyUI-LLM DeepSeek",
                "ComfyUI-LLM Agent SDK",
            },
        )

    def test_agent_node_has_stable_contract(self):
        inputs = nodes.AgentSDKNode.INPUT_TYPES()
        self.assertIn("prompt", inputs["required"])
        self.assertIn("skill_override", inputs["required"])
        self.assertIn("images", inputs["optional"])
        self.assertNotIn("resume_state", inputs["optional"])
        self.assertEqual(inputs["hidden"]["unique_id"], "UNIQUE_ID")
        self.assertEqual(inputs["required"]["image_model"][0], ["gpt-image-2"])
        self.assertTrue(inputs["required"]["publish_to_oss"][1]["default"])
        self.assertEqual(inputs["required"]["skill_override"][0][0], "自动选择")
        self.assertIn("批量AI换装", inputs["required"]["skill_override"][0])
        self.assertEqual(
            nodes.AgentSDKNode.RETURN_NAMES,
            ("images", "text", "output_path", "artifacts_json", "state_json"),
        )

    def test_only_vision_nodes_have_image_input(self):
        for cls in (
            nodes.GPTLLMNode,
            nodes.ClaudeLLMNode,
            nodes.GeminiLLMNode,
        ):
            self.assertIn("image", cls.INPUT_TYPES()["optional"])
        self.assertNotIn("optional", nodes.DeepSeekLLMNode.INPUT_TYPES())

    def test_chinese_skill_labels_map_to_runtime_names(self):
        self.assertEqual(nodes._skill_value("批量AI换装"), "batch-ai-tryon")
        self.assertEqual(nodes._skill_value("自动选择"), "auto")
        self.assertEqual(nodes._skill_value("world-buyer"), "world-buyer")

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

    def test_agent_node_returns_artifacts_and_state(self):
        with tempfile.TemporaryDirectory() as temp:
            config = {
                "allowed_output_roots": [temp],
                "oss_enabled": False,
            }
            with (
                patch.object(nodes, "load_config", return_value=config),
                patch.object(
                    nodes,
                    "resolve_runtime_config",
                    return_value={
                        "api_key": "test",
                        "timeout": 10,
                        "max_retries": 0,
                        "retry_delay": 0,
                    },
                ),
                patch.object(nodes, "AgentWorkerClient", FakeAgentWorkerClient),
            ):
                result = asyncio.run(
                    nodes.AgentSDKNode().run_agent(
                        prompt="设计一件外套",
                        agent_model="gpt-5.5",
                        skill_override="auto",
                        image_model="auto",
                        thinking_level="medium",
                        output_dir=temp,
                        max_agent_turns=12,
                        publish_to_oss=False,
                    )
                )
        images, text, output_path, artifacts, state = result
        self.assertEqual(text, "完成")
        self.assertTrue(output_path.endswith("outputs"))
        self.assertEqual(json.loads(artifacts)[0]["width"], 8)
        self.assertEqual(json.loads(state)["status"], "completed")
        self.assertEqual(json.loads(state)["delivery_mode"], "image")
        self.assertEqual(tuple(images.shape), (1, 6, 8, 3))

    def test_agent_node_allows_text_only_skill_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            config = {"allowed_output_roots": [temp], "oss_enabled": False}
            with (
                patch.object(nodes, "load_config", return_value=config),
                patch.object(
                    nodes,
                    "resolve_runtime_config",
                    return_value={
                        "api_key": "test",
                        "timeout": 10,
                        "max_retries": 0,
                        "retry_delay": 0,
                    },
                ),
                patch.object(nodes, "AgentWorkerClient", FakeTextAgentWorkerClient),
            ):
                result = asyncio.run(
                    nodes.AgentSDKNode().run_agent(
                        prompt="只输出文字买手分析",
                        agent_model="gpt-5.5",
                        skill_override="世界服装买手",
                        image_model="gpt-image-2",
                        thinking_level="medium",
                        output_dir=temp,
                        max_agent_turns=12,
                        publish_to_oss=False,
                    )
                )
        images, text, _, artifacts, state = result
        self.assertEqual(text, "纯文字买手分析")
        self.assertEqual(json.loads(artifacts), [])
        self.assertEqual(json.loads(state)["delivery_mode"], "text")
        self.assertEqual(tuple(images.shape), (1, 64, 64, 3))


if __name__ == "__main__":
    unittest.main()
