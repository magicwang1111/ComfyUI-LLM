import asyncio
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


if __name__ == "__main__":
    unittest.main()
