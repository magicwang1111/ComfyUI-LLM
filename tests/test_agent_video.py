import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import av
import numpy as np
from agents.tool_context import ToolContext

from _loader import import_module

runtime_module = import_module("agent_runtime")
artifact_store = import_module("artifact_store")
nodes = import_module("nodes")
video_nodes = import_module("video_nodes")


class AgentVideoTests(unittest.TestCase):
    @unittest.skipIf(nodes.InputImpl is None, "Requires the ComfyUI native video API")
    def test_native_video_save_preserves_video_and_audio_streams(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.mp4"
            with av.open(str(source), "w") as container:
                video = container.add_stream("libx264", rate=10)
                video.width = video.height = 32
                video.pix_fmt = "yuv420p"
                audio = container.add_stream("aac", rate=48000)
                audio.layout = "mono"
                for index in range(10):
                    frame = av.VideoFrame.from_ndarray(np.full((32, 32, 3), index * 20, dtype=np.uint8), format="rgb24")
                    container.mux(video.encode(frame))
                container.mux(video.encode())
                samples = (0.2 * np.sin(2 * np.pi * 440 * np.arange(48000) / 48000)).astype(np.float32).reshape(1, -1)
                frame = av.AudioFrame.from_ndarray(samples, format="fltp", layout="mono")
                frame.sample_rate = 48000
                container.mux(audio.encode(frame))
                container.mux(audio.encode())

            paths = SimpleNamespace(
                get_output_directory=lambda: temp,
                get_save_image_path=lambda prefix, root: (temp, "LLM_test", 1, "", prefix),
            )
            with patch.object(video_nodes, "folder_paths", paths):
                result = video_nodes.LLMVideoOutput().save(nodes.InputImpl.VideoFromFile(str(source)))
            saved = result["result"][0]
            for stream in ("video", "audio"):
                with av.open(str(source)) as original, av.open(saved) as output:
                    expected = [frame.to_ndarray() for frame in original.decode(**{stream: 0})]
                    actual = [frame.to_ndarray() for frame in output.decode(**{stream: 0})]
                    self.assertGreater(len(expected), 0)
                    self.assertEqual(len(actual), len(expected))
                    for original_frame, saved_frame in zip(expected, actual):
                        np.testing.assert_array_equal(original_frame, saved_frame)

    def test_download_script_registers_video_and_video_only_delivery_succeeds(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_path = root / "tiktok-fashion-video"
            scripts = skill_path / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "download_video.py").write_text(
                "import sys\nfrom pathlib import Path\n"
                "(Path(sys.argv[2]) / 'final.mp4').write_bytes(b'test-video')\n",
                encoding="utf-8",
            )
            skill = SimpleNamespace(name="tiktok-fashion-video", path=skill_path, instructions="Generate video.")
            runtime = runtime_module.AgentRuntime.__new__(runtime_module.AgentRuntime)
            runtime.artifact_store = artifact_store.LocalArtifactStore(root / "outputs", flat_outputs=True)
            runtime.allowed_paths = [runtime.artifact_store.outputs_dir]
            runtime.script_python = sys.executable
            runtime.script_output_paths = set()
            runtime.events = []
            runtime.event_callback = None
            script_tool = next(tool for tool in runtime._tools(skill, []) if tool.name == "run_skill_script")
            arguments = json.dumps({
                "script_name": "download_video.py",
                "arguments": ["--run-dir", str(runtime.artifact_store.outputs_dir)],
            })
            context = ToolContext(None, tool_name="run_skill_script", tool_call_id="video", tool_arguments=arguments)
            result = json.loads(asyncio.run(script_tool.on_invoke_tool(context, arguments)))
            self.assertEqual(result["artifact"]["content_type"], "video/mp4")
            self.assertEqual(Path(result["artifact"]["path"]).name, "final.mp4")
            asyncio.run(script_tool.on_invoke_tool(context, arguments))
            self.assertEqual(len(runtime.artifact_store.records), 1)

            runtime.registry = SimpleNamespace(get=lambda name: skill)
            runtime.model = "test-model"
            runtime.thinking_level = "high"
            runtime.max_turns = 12
            runtime.hooks = None
            decision = SimpleNamespace(skill_name=skill.name, mode="video")
            with patch.object(runtime_module.Runner, "run", AsyncMock(return_value=SimpleNamespace(final_output="视频完成"))) as run:
                self.assertEqual(asyncio.run(runtime.execute("生成视频", decision, [])), "视频完成")
                self.assertIsNone(run.call_args.args[0].model_settings.tool_choice)
                self.assertIn("video artifacts required", run.call_args.args[0].instructions)
                runtime.artifact_store.records = []
                run.return_value = SimpleNamespace(final_output="缺少已验证的商品图和视频服务登录配置。")
                with self.assertRaisesRegex(ValueError, "缺少已验证的商品图"):
                    asyncio.run(runtime.execute("生成视频", decision, []))
                self.assertEqual(runtime.events[-1]["message"], run.return_value.final_output)

            (scripts / "fail.py").write_text(
                "import sys\nprint('Missing workflow file', file=sys.stderr)\nsys.exit(2)\n",
                encoding="utf-8",
            )
            failed_arguments = json.dumps({"script_name": "fail.py", "arguments": []})
            failed = json.loads(asyncio.run(script_tool.on_invoke_tool(context, failed_arguments)))
            self.assertEqual(failed["returncode"], 2)
            self.assertEqual(runtime.events[-1]["event"], "tool_error")
            self.assertIn("Missing workflow file", runtime.events[-1]["message"])

            (scripts / "collect_product.py").write_text(
                "import sys\nfrom PIL import Image\nImage.new('RGB', (20, 30)).save(sys.argv[2])\n",
                encoding="utf-8",
            )
            reference_args = json.dumps({"script_name": "collect_product.py", "arguments": ["--output", str(runtime.artifact_store.outputs_dir / 'product.jpg')]})
            reference = json.loads(asyncio.run(script_tool.on_invoke_tool(context, reference_args)))
            self.assertEqual(reference['artifact']['kind'], 'reference')
            inspected = runtime._output_by_name(runtime.artifact_store.records, 'product.jpg')
            self.assertEqual(inspected.kind, 'reference')

    def test_agent_exposes_all_successful_videos_and_persists_video_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            records = [
                artifact_store.ArtifactRecord(path=str(Path(temp) / name), content_type=mime, status=status).disk_dict()
                for name, mime, status in (
                    ("first.mp4", "video/mp4", "success"),
                    ("second.mp4", "video/mp4", "success"),
                    ("failed.mp4", "video/mp4", "failed"),
                )
            ]
            worker = SimpleNamespace(run=AsyncMock(return_value={"route": {}, "text": "视频完成", "artifacts": records}))
            with (
                patch.object(nodes, "load_config", return_value={"allowed_output_roots": [temp]}),
                patch.object(nodes, "resolve_runtime_config", return_value={"timeout": 10}),
                patch.object(nodes, "AgentWorkerClient", return_value=worker),
                patch.object(nodes, "InputImpl", SimpleNamespace(VideoFromFile=lambda path: ("video", path))),
            ):
                result = asyncio.run(nodes.AgentSDKNode().run_agent(
                    prompt="生成视频", agent_model="gpt-6-astra", skill_override="tiktok-fashion-video",
                    image_model="gpt-image-2", thinking_level="high", output_dir=temp,
                    max_agent_turns=12, publish_to_oss=False,
                ))
            self.assertEqual(result[4], [("video", record["path"]) for record in records[:2]])
            state = json.loads(next(Path(temp).rglob("state.json")).read_text("utf-8"))
            self.assertEqual(state["delivery_mode"], "video")

    def test_video_output_saves_by_default_and_returns_local_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            class Video:
                def save_to(self, path, format, codec):
                    self.parameters = (format, codec)
                    Path(path).write_bytes(b"video-and-audio")

            video = Video()
            paths = SimpleNamespace(
                get_output_directory=lambda: temp,
                get_save_image_path=lambda prefix, root: (temp, "LLM_test", 1, "video", prefix),
            )
            with patch.object(video_nodes, "folder_paths", paths):
                result = video_nodes.LLMVideoOutput().save(video)
            self.assertEqual(video.parameters, ("mp4", "auto"))
            self.assertEqual(Path(result["result"][0]).read_bytes(), b"video-and-audio")
            self.assertEqual(result["ui"]["images"], [
                {"filename": "LLM_test_00001_.mp4", "subfolder": "video", "type": "output"},
            ])
            self.assertEqual(result["ui"]["animated"], (True,))


if __name__ == "__main__":
    unittest.main()
