import asyncio
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
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
            flat_outputs=bool(job.get("flat_outputs")),
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


class CapturingAgentWorkerClient(FakeAgentWorkerClient):
    last_job = None

    async def run(self, job, work_dir, on_event=None):
        type(self).last_job = job
        return await super().run(job, work_dir, on_event=on_event)


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
        self.assertEqual(
            package.NODE_DISPLAY_NAME_MAPPINGS["ComfyUI-LLM Agent SDK"],
            "ComfyUI-LLM Agent Node",
        )

    def test_agent_node_has_stable_contract(self):
        inputs = nodes.AgentSDKNode.INPUT_TYPES()
        self.assertIn("prompt", inputs["required"])
        self.assertIn("skill_override", inputs["required"])
        self.assertIn("images", inputs["optional"])
        if nodes.io is not None:
            self.assertIn("reference_images", inputs["optional"])
        self.assertNotIn("resume_state", inputs["optional"])
        self.assertIn(inputs["hidden"]["unique_id"], {"UNIQUE_ID", ("UNIQUE_ID",)})
        image_model_input = inputs["required"]["image_model"]
        image_model_options = (
            image_model_input[1]["options"]
            if image_model_input[0] == "COMBO"
            else image_model_input[0]
        )
        self.assertEqual(image_model_options, ["gpt-image-2"])
        self.assertTrue(inputs["required"]["publish_to_oss"][1]["default"])
        skill_input = inputs["required"]["skill_override"]
        skill_options = skill_input[1]["options"] if skill_input[0] == "COMBO" else skill_input[0]
        self.assertEqual(skill_options[0], "自动选择")
        self.assertIn("批量AI换装", skill_options)
        self.assertEqual(
            tuple(nodes.AgentSDKNode.RETURN_NAMES),
            ("images", "text"),
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
            artifacts_path = next(Path(temp).rglob("artifacts.json"))
            state_path = artifacts_path.with_name("state.json")
            artifact_data = json.loads(artifacts_path.read_text("utf-8"))
            state_data = json.loads(state_path.read_text("utf-8"))
            artifacts_share_output_dir = Path(artifact_data[0]["path"]).parent.samefile(
                artifacts_path.parent
            )
        images, text = result
        self.assertEqual(text, "完成")
        self.assertEqual(artifact_data[0]["width"], 8)
        self.assertNotIn("signed_url", artifact_data[0])
        self.assertTrue(artifacts_share_output_dir)
        self.assertEqual(state_data["status"], "completed")
        self.assertEqual(state_data["delivery_mode"], "image")
        self.assertEqual(tuple(images.shape), (1, 6, 8, 3))

    def test_dynamic_inputs_preserve_dimensions_and_image_zero_sets_size_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            config = {"allowed_output_roots": [temp], "oss_enabled": False}
            image_zero = np.zeros((1, 16, 9, 3), dtype=np.float32)
            image_one = np.zeros((1, 8, 12, 3), dtype=np.float32)
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
                patch.object(nodes, "AgentWorkerClient", CapturingAgentWorkerClient),
            ):
                asyncio.run(
                    nodes.AgentSDKNode().run_agent(
                        prompt="test",
                        agent_model="gpt-5.5",
                        skill_override="auto",
                        image_model="gpt-image-2",
                        thinking_level="medium",
                        output_dir=temp,
                        max_agent_turns=12,
                        publish_to_oss=False,
                        reference_images={"image1": image_one, "image0": image_zero},
                    )
                )
            job = CapturingAgentWorkerClient.last_job
            saved_paths = [Path(item) for item in job["input_paths"]]
            with Image.open(saved_paths[0]) as first, Image.open(saved_paths[1]) as second:
                saved_sizes = (first.size, second.size)

        self.assertEqual(saved_sizes, ((9, 16), (12, 8)))
        self.assertEqual(job["size_reference_path"], str(saved_paths[0]))

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
            artifacts_path = next(Path(temp).rglob("artifacts.json"))
            state_path = artifacts_path.with_name("state.json")
            artifact_data = json.loads(artifacts_path.read_text("utf-8"))
            state_data = json.loads(state_path.read_text("utf-8"))
        images, text = result
        self.assertEqual(text, "纯文字买手分析")
        self.assertEqual(artifact_data, [])
        self.assertEqual(state_data["delivery_mode"], "text")
        self.assertEqual(tuple(images.shape), (1, 64, 64, 3))


if __name__ == "__main__":
    unittest.main()
