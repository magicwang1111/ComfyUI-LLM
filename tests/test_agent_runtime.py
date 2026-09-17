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


class UsageTests(unittest.TestCase):
    def test_agent_usage_accumulates_per_response_cost(self):
        runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
        runtime.agent_model = "gpt-5.6-terra"
        runtime.usage = {
            "estimated_cost_usd": 0.0,
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "request_count": 0,
        }
        first = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=1_000,
                output_tokens=100,
                input_tokens_details=SimpleNamespace(cached_tokens=200),
            )
        )
        second = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=2_000,
                output_tokens=200,
                input_tokens_details=SimpleNamespace(cached_tokens=0),
            )
        )

        runtime._add_response_usage(first)
        runtime._add_response_usage(second)
        summary = runtime.usage_summary()

        self.assertEqual(summary["request_count"], 2)
        self.assertEqual(summary["input_tokens"], 3_000)
        self.assertEqual(summary["cached_input_tokens"], 200)
        self.assertEqual(summary["output_tokens"], 300)
        self.assertAlmostEqual(summary["estimated_cost_usd"], 0.01155)


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

    def test_faceless_repeated_retries_keep_three_deliverables(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            names = [
                "style_1_polished_commuter.png",
                "style_2_relaxed_weekend.png",
                "style_3_city_athleisure.png",
                "style_1_polished_commuter_重做.png",
                "style_3_city_athleisure_重做.png",
                "style_1_polished_commuter_final.png",
                "style_3_city_athleisure_final.png",
                "style_1_polished_commuter_final2.png",
                "style_3_city_athleisure_final2.png",
                "style_1_polished_commuter_final3.png",
            ]
            candidates = [self.add_output(runtime, name) for name in names]
            input_path = runtime.artifact_store.inputs_dir / "reference.png"
            input_path.write_bytes(b"reference")
            reference = runtime.artifact_store.add(input_path, kind="input")
            notes = self.add_output(runtime, "notes.txt")

            kept = runtime._enforce_output_contract(
                "faceless-outfit-stylist", [], candidates
            )

            self.assertEqual(kept, [candidates[9], candidates[1], candidates[8]])
            self.assertEqual(runtime.artifact_store.records, [reference, notes] + kept)
            for item in candidates:
                self.assertEqual(Path(item.path).exists(), item in kept)
            self.assertTrue(input_path.exists())
            self.assertTrue(Path(notes.path).exists())
            manifest = runtime.artifact_store.write_manifest("faceless-outfit-stylist")
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                [item["path"] for item in payload["artifacts"] if item["content_type"].startswith("image/") and item["kind"] == "output"],
                [item.path for item in kept],
            )

    def test_retry_chains_use_registration_order_and_preserve_unrelated_images(self):
        for names in (
            ["look.png", "look_final10.png", "look_final2.png"],
            ["look.png", "look_retry2.png", "look_retry2_final3.png"],
            ["look_final.png", "look_final_重做2.png", "look_final_重做2_final_3.png"],
            ["look_final2.png", "look_final3.png"],
            ["look.png", "look_FINAL2.png", "look_final2_2.png"],
            ["look.png", "look_v2.png", "look_final_v3.png"],
        ):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temp:
                runtime = self.runtime_with_store(temp)
                candidates = [self.add_output(runtime, name) for name in names]
                unrelated = [self.add_output(runtime, name) for name in (
                    "look_finale.png", "look_retryable.png", "look_2.png", "other_final2.png",
                )]
                kept = runtime._enforce_output_contract(
                    "outfit-flatlay-stylist", [], candidates + unrelated
                )
                self.assertEqual(kept, candidates[-1:] + unrelated)
                self.assertEqual(runtime.artifact_store.records, kept)
                for item in candidates + unrelated:
                    self.assertEqual(Path(item.path).exists(), item in kept)
                self.assertEqual(runtime._replace_named_retries(kept), kept)

    def test_numbered_slot_recognizes_numbered_retry_with_changed_description(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime_with_store(temp)
            original = self.add_output(runtime, "01_commuter.png")
            revised = self.add_output(runtime, "01_polished_final2.png")
            kept = runtime._enforce_output_contract(
                "outfit-flatlay-stylist", [], [original, revised]
            )
            self.assertEqual(kept, [revised])
            self.assertFalse(Path(original.path).exists())

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
    def test_outfit_swap_uses_reordered_scene_as_size_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
            runtime.artifact_store = artifact_store.LocalArtifactStore(temp, flat_outputs=True)
            runtime.events = []
            runtime.event_callback = None
            runtime.image_model = "gpt-image-2"
            runtime.mask_path = None

            inputs = []
            for index in range(5):
                path = Path(temp) / f"input-{index + 1}.png"
                Image.new("RGB", (100 + index, 200), "white").save(path)
                inputs.append(path)
            runtime.size_reference_path = inputs[0]

            class ImageClient:
                def __init__(self):
                    self.size_reference = None

                async def edit(self, **kwargs):
                    self.size_reference = kwargs["size_reference"]
                    return [Image.new("RGB", (8, 8), "white")]

            runtime.image_client = ImageClient()
            skill = SimpleNamespace(name="fashion-model-outfit-swap", path=Path(temp))
            tools = runtime._tools(skill, inputs)
            edit_tool = next(tool for tool in tools if tool.name == "edit_images")
            arguments = json.dumps(
                {
                    "prompt": "test",
                    "image_indices": [5, 1, 2, 3, 4],
                    "n": 1,
                    "size": "auto",
                    "output_name": "result.png",
                }
            )

            asyncio.run(
                edit_tool.on_invoke_tool(
                    ToolContext(
                        None,
                        tool_name="edit_images",
                        tool_call_id="edit-call",
                        tool_arguments=arguments,
                    ),
                    arguments,
                )
            )

            self.assertEqual(runtime.image_client.size_reference, inputs[4])

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

    def test_inspection_can_compare_generated_image_with_source_input(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = agent_runtime.AgentRuntime.__new__(agent_runtime.AgentRuntime)
            runtime.artifact_store = artifact_store.LocalArtifactStore(temp, flat_outputs=True)
            input_path = Path(temp) / "scene.png"
            output_path = runtime.artifact_store.outputs_dir / "candidate.png"
            Image.new("RGB", (3, 4), "blue").save(input_path)
            Image.new("RGB", (3, 4), "white").save(output_path)
            runtime.artifact_store.add(output_path, width=3, height=4)
            runtime.events = []
            runtime.event_callback = None
            runtime.agent_model = "test-model"

            class Responses:
                def __init__(self):
                    self.input = None

                async def create(self, **kwargs):
                    self.input = kwargs["input"]
                    return SimpleNamespace(output_text="场景一致。")

            responses = Responses()
            runtime.client = SimpleNamespace(responses=responses)
            tools = runtime._tools(SimpleNamespace(path=Path(temp)), [input_path])
            inspect_tool = next(tool for tool in tools if tool.name == "inspect_generated_image")
            arguments = json.dumps(
                {
                    "image_name": "candidate.png",
                    "checklist": "对比场景和构图",
                    "reference_image_indices": [1],
                }
            )

            result = asyncio.run(
                inspect_tool.on_invoke_tool(
                    ToolContext(
                        None,
                        tool_name="inspect_generated_image",
                        tool_call_id="compare-call",
                        tool_arguments=arguments,
                    ),
                    arguments,
                )
            )

            content = responses.input[0]["content"]
            self.assertEqual(result, "场景一致。")
            self.assertEqual(
                [item["type"] for item in content],
                ["input_text", "input_text", "input_image", "input_text", "input_image"],
            )

    def test_outfit_swap_allows_only_one_inspection_per_task(self):
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
                def __init__(self):
                    self.calls = 0

                async def create(self, **kwargs):
                    self.calls += 1
                    return SimpleNamespace(output_text="ok")

            responses = Responses()
            runtime.client = SimpleNamespace(responses=responses)
            runtime._record = agent_runtime.AgentRuntime._record.__get__(runtime)
            runtime._output_by_name = agent_runtime.AgentRuntime._output_by_name

            skill = SimpleNamespace(
                name="fashion-model-outfit-swap",
                path=Path(temp),
            )
            tools = runtime._tools(skill, [])
            inspect_tool = next(tool for tool in tools if tool.name == "inspect_generated_image")
            arguments = '{"image_name":"checked.png","checklist":"check"}'

            first = asyncio.run(
                inspect_tool.on_invoke_tool(
                    ToolContext(
                        None,
                        tool_name="inspect_generated_image",
                        tool_call_id="first-call",
                        tool_arguments=arguments,
                    ),
                    arguments,
                )
            )
            self.assertEqual(first, "ok")

            second = asyncio.run(
                inspect_tool.on_invoke_tool(
                    ToolContext(
                        None,
                        tool_name="inspect_generated_image",
                        tool_call_id="second-call",
                        tool_arguments=arguments,
                    ),
                    arguments,
                )
            )
            self.assertIn("at most one image inspection", second)
            self.assertEqual(responses.calls, 1)

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
