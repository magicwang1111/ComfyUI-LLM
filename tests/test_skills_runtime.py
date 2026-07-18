import tempfile
import unittest
from pathlib import Path

from _loader import import_module

skills_runtime = import_module("skills_runtime")


class SkillRegistryTests(unittest.TestCase):
    def test_discovers_all_current_skills(self):
        registry = skills_runtime.SkillRegistry()
        self.assertEqual(len(registry.skills), 11)
        self.assertIn("batch-ai-tryon", registry.skills)
        self.assertIn("fashion-model-outfit-swap", registry.skills)
        self.assertIn("world-buyer", registry.skills)
        self.assertEqual(registry.errors, [])

    def test_resource_cannot_escape_skill_directory(self):
        skill = skills_runtime.SkillRegistry().get("outfit-flatlay-stylist")
        with self.assertRaisesRegex(ValueError, "not allowed"):
            skill.read_resource("../../../../config.local.json")

    def test_bad_and_duplicate_skills_are_isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("one", "two"):
                folder = root / name
                folder.mkdir()
                (folder / "SKILL.md").write_text(
                    "---\nname: duplicate\ndescription: test\n---\nbody",
                    encoding="utf-8",
                )
            (root / "bad").mkdir()
            (root / "bad" / "SKILL.md").write_text("no frontmatter", encoding="utf-8")
            registry = skills_runtime.SkillRegistry(root)
        self.assertEqual(list(registry.skills), ["duplicate"])
        self.assertEqual(len(registry.errors), 2)


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.registry = skills_runtime.SkillRegistry()

    def route(self, prompt, **kwargs):
        return skills_runtime.route_with_rules(self.registry, prompt, **kwargs)

    def test_routes_representative_tasks(self):
        cases = {
            "给这个模特批量换装": "batch-ai-tryon",
            "生成服装白底平铺图": "batch-clothing-white-bg-images",
            "严格按模板做详情页": "batch-apparel-detail-pages",
            "分析这款衣服的爆款基因": "hot-style-analyzer",
            "帮我做环球买手找款": "world-buyer",
            "做一个高级 showroom 陈列": "clothing-display-image-to-image",
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(self.route(prompt, image_count=1).skill_name, expected)

    def test_print_defaults_to_gene_extension(self):
        decision = self.route("根据这张印花做衍生", image_count=1)
        self.assertEqual(decision.skill_name, "print-pattern-derivation")
        self.assertEqual(decision.mode, "1-gene-extension")

    def test_missing_visual_input_is_reported(self):
        decision = self.route("生成白底图")
        self.assertTrue(decision.needs_input)
        self.assertTrue(decision.missing_inputs)
        self.assertIn("请提供 IMAGE 输入", decision.missing_inputs[0])

    def test_override_wins(self):
        decision = self.route(
            "随便写的请求",
            skill_override="fashion-design-analysis",
        )
        self.assertEqual(decision.skill_name, "fashion-design-analysis")
        self.assertEqual(decision.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
