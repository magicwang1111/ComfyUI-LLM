import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agents.tool_context import ToolContext
from PIL import Image

from _loader import import_module

agent_runtime = import_module("agent_runtime")
artifact_store = import_module("artifact_store")


class OutputContractTests(unittest.TestCase):
    def runtime_with_store(self, root):
        runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
        runtime.artifact_store = artifact_store.LocalArtifactStore(root, flat_outputs=True)
        runtime.events = []
        runtime.event_callback = None
        return runtime

    @staticmethod
    def add_output(runtime, filename):
        path = runtime.artifact_store.outputs_dir / filename
        path.write_bytes(filename.encode("utf-8"))
        return runtime.artifact_store.add(path, width=1, height=1)

    def test_date_prefixed_retry_replaces_original_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            look_03 = self.add_output(
                runtime,
                "20260717-0003_cobalt-puffer-feminine-city-look03_flatlay.png",
            )
            look_02 = self.add_output(
                runtime,
                "20260717-0002_cobalt-puffer-apres-ski-look02_flatlay.png",
            )
            rejected_look_01 = self.add_output(
                runtime,
                "20260717-0001_cobalt-puffer-urban-look01_flatlay.png",
            )
            final_look_01 = self.add_output(
                runtime,
                "20260717-0001_cobalt-puffer-urban-look01_flatlay_重做.png",
            )

            kept = runtime._enforce_output_contract(
                "outfit-flatlay-stylist", [], list(runtime.artifact_store.records)
            )

            self.assertEqual(
                [Path(item.path).name for item in kept],
                [
                    "20260717-0001_cobalt-puffer-urban-look01_flatlay_重做.png",
                    "20260717-0002_cobalt-puffer-apres-ski-look02_flatlay.png",
                    "20260717-0003_cobalt-puffer-feminine-city-look03_flatlay.png",
                ],
            )
            self.assertEqual(runtime.artifact_store.records, kept)
            self.assertFalse(Path(rejected_look_01.path).exists())
            self.assertTrue(Path(final_look_01.path).exists())
            self.assertTrue(Path(look_02.path).exists())
            self.assertTrue(Path(look_03.path).exists())

    def test_timestamp_named_retry_replaces_original_without_numeric_slot(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            rejected = self.add_output(
                runtime, "20260717-1405_cobalt-puffer-flatlay.png"
            )
            final = self.add_output(
                runtime, "20260717-1405_cobalt-puffer-flatlay_final.png"
            )

            kept = runtime._enforce_output_contract(
                "outfit-flatlay-stylist", [], list(runtime.artifact_store.records)
            )

            self.assertEqual(
                [Path(item.path).name for item in kept], [Path(final.path).name]
            )
            self.assertEqual(runtime.artifact_store.records, kept)
            self.assertFalse(Path(rejected.path).exists())
            self.assertTrue(Path(final.path).exists())

    def test_fashion_swap_keeps_only_registered_script_output(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            candidates = [
                self.add_output(runtime, name)
                for name in (
                    "换装.png",
                    "换装_final.png",
                    "换装_终稿.png",
                    "换装_交付_final.png",
                )
            ]
            normalized = self.add_output(runtime, "换装_最终2K.png")
            runtime.script_output_paths = {str(Path(normalized.path).resolve())}

            kept = runtime._enforce_output_contract(
                "fashion-model-outfit-swap",
                [],
                list(runtime.artifact_store.records),
            )

            self.assertEqual(kept, [normalized])
            self.assertEqual(runtime.artifact_store.records, [normalized])
            for candidate in candidates:
                self.assertFalse(Path(candidate.path).exists())
            self.assertTrue(Path(normalized.path).exists())

    def test_numbered_slot_handles_date_prefix_without_using_time_as_slot(self):
        self.assertEqual(
            agent_runtime.AgentRuntime._numbered_output_slot(
                SimpleNamespace(path="20260717-0001_cobalt-puffer-flatlay.png")
            ),
            1,
        )
        self.assertEqual(
            agent_runtime.AgentRuntime._numbered_output_slot(
                SimpleNamespace(path="20260717-1405-0001_cobalt-puffer-flatlay.png")
            ),
            1,
        )
        self.assertIsNone(
            agent_runtime.AgentRuntime._numbered_output_slot(
                SimpleNamespace(path="20260717-1405_cobalt-puffer-flatlay.png")
            )
        )

    def test_world_buyer_keeps_latest_five_cards_and_latest_contact_sheet(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            original = [
                self.add_output(runtime, f"world-buyer-product-{slot:02d}.png")
                for slot in range(1, 6)
            ]
            final_card_01 = self.add_output(
                runtime, "world-buyer-product-01_final.png"
            )
            contact_sheets = [
                self.add_output(runtime, name)
                for name in (
                    "world-buyer-contact-sheet.png",
                    "world-buyer-contact-sheet_final.png",
                    "world-buyer-contact-sheet_candidateA.png",
                    "world-buyer-contact-sheet_candidateB.png",
                    "world-buyer-contact-sheet_final_deliverable.png",
                )
            ]

            kept = runtime._enforce_output_contract(
                "world-buyer", [], list(runtime.artifact_store.records)
            )

            kept_names = [Path(item.path).name for item in kept]
            self.assertEqual(
                kept_names,
                [
                    "world-buyer-product-01_final.png",
                    "world-buyer-product-02.png",
                    "world-buyer-product-03.png",
                    "world-buyer-product-04.png",
                    "world-buyer-product-05.png",
                    "world-buyer-contact-sheet_final_deliverable.png",
                ],
            )
            self.assertEqual(runtime.artifact_store.records, kept)
            self.assertFalse(Path(original[0].path).exists())
            self.assertTrue(Path(final_card_01.path).exists())
            for candidate in contact_sheets[:-1]:
                self.assertFalse(Path(candidate.path).exists())
            self.assertTrue(Path(contact_sheets[-1].path).exists())

    def test_world_buyer_rejects_incomplete_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            for slot in range(1, 5):
                self.add_output(runtime, f"world-buyer-product-{slot:02d}.png")
            self.add_output(runtime, "world-buyer-contact-sheet.png")

            with self.assertRaisesRegex(ValueError, "product-05"):
                runtime._enforce_output_contract(
                    "world-buyer", [], list(runtime.artifact_store.records)
                )


class ModelSettingsTests(unittest.TestCase):
    def test_reasoning_summary_is_detailed(self):
        runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
        runtime.thinking_level = "high"

        settings = runtime._settings()

        self.assertEqual(settings.reasoning.summary, "detailed")


class InspectionProgressTests(unittest.TestCase):
    def test_output_lookup_uses_exact_filename_not_completion_order(self):
        records = [
            SimpleNamespace(kind="output", path="01_first.png"),
            SimpleNamespace(kind="output", path="03_third.png"),
            SimpleNamespace(kind="output", path="02_second.png"),
        ]

        selected = agent_runtime.AgentRuntime._output_by_name(
            records, "02_second.png"
        )

        self.assertEqual(selected.path, "02_second.png")

    def test_inspection_result_is_emitted_as_progress_event(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
            runtime.artifact_store = artifact_store.LocalArtifactStore(temp, flat_outputs=True)
            image_path = runtime.artifact_store.outputs_dir / "checked.png"
            Image.new("RGB", (1, 1), "white").save(image_path)
            runtime.artifact_store.add(image_path, width=1, height=1)
            runtime.events = []
            runtime.event_callback = None
            runtime.agent_model = "test-model"

            class Responses:
                async def create(self, **kwargs):
                    return SimpleNamespace(output_text="图片符合检查标准。")

            runtime.client = SimpleNamespace(responses=Responses())
            runtime._record = agent_runtime.AgentRuntime._record.__get__(runtime)
            runtime._output_by_name = agent_runtime.AgentRuntime._output_by_name

            tools = runtime._tools(SimpleNamespace(path=Path(temp)), [])
            inspect_tool = next(tool for tool in tools if tool.name == "inspect_generated_image")
            result = asyncio.run(
                inspect_tool.on_invoke_tool(
                    ToolContext(
                        None,
                        tool_name="inspect_generated_image",
                        tool_call_id="test-call",
                        tool_arguments='{"image_name":"checked.png","checklist":"检查完整性"}',
                    ),
                    '{"image_name":"checked.png","checklist":"检查完整性"}',
                )
            )

            self.assertEqual(result, "图片符合检查标准。")
            self.assertIn(
                {
                    "event": "inspection_result",
                    "message": "图片复核结果（checked.png）：\n图片符合检查标准。",
                    "tool": "inspect_generated_image",
                    "image_name": "checked.png",
                },
                runtime.events,
            )

    def test_skill_script_registers_normalized_output_as_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
            runtime.artifact_store = artifact_store.LocalArtifactStore(temp, flat_outputs=True)
            runtime.allowed_paths = [Path(temp).resolve()]
            runtime.script_python = sys.executable
            runtime.script_output_paths = set()
            runtime.events = []
            runtime.event_callback = None

            base_path = runtime.artifact_store.outputs_dir / "base.png"
            input_path = runtime.artifact_store.outputs_dir / "candidate.png"
            output_path = runtime.artifact_store.outputs_dir / "final-2k.png"
            Image.new("RGB", (300, 500), "white").save(base_path)
            Image.new("RGB", (600, 600), "blue").save(input_path)

            skill_path = (
                Path(__file__).resolve().parents[1]
                / "skills"
                / "fashion-model-outfit-swap"
            )
            tools = runtime._tools(SimpleNamespace(path=skill_path), [])
            script_tool = next(tool for tool in tools if tool.name == "run_skill_script")
            arguments = {
                "script_name": "normalize_2k.py",
                "arguments": [
                    "--base",
                    str(base_path),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
            }
            tool_arguments = json.dumps(arguments)

            result = asyncio.run(
                script_tool.on_invoke_tool(
                    ToolContext(
                        None,
                        tool_name="run_skill_script",
                        tool_call_id="test-call",
                        tool_arguments=tool_arguments,
                    ),
                    tool_arguments,
                )
            )
            result_data = json.loads(result)

            self.assertEqual(result_data["returncode"], 0)
            self.assertEqual(Path(result_data["artifact"]["path"]), output_path)
            self.assertEqual(
                (
                    result_data["artifact"]["width"],
                    result_data["artifact"]["height"],
                ),
                (1229, 2048),
            )
            self.assertEqual(
                [Path(item.path) for item in runtime.artifact_store.records],
                [output_path],
            )
            self.assertEqual(runtime.script_output_paths, {str(output_path.resolve())})


if __name__ == "__main__":
    unittest.main()
