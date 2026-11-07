import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from _loader import import_module

fashion = import_module('fashion_prompt')


def sample_prompt():
    titles = ['服装判断', '基础设定', '主体与服装', '场景', '镜头与情绪总要求', '三分镜完整脚本',
              '完整英文口播', '完整中文参考', '整体表演要求', '声音规范', '人物、服装与场景一致性',
              'Negative Prompt', '最终执行要求']
    return '\n\n'.join(f'## {index}、{title}\n' + ('Look at this neckline!' if index == 7 else '具体内容。')
                        for index, title in enumerate(titles, 1))


class FashionPromptTests(unittest.TestCase):
    def test_source_edits_are_visible_without_reloading_module(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'rules.md'
            with patch.object(fashion, 'RULES_PATH', source), patch.object(fashion, 'RULES_DIR', source.parent):
                source.write_text('第一版规范', encoding='utf-8-sig')
                first = fashion.review_prompt('prompt')
                source.write_text('第二版规范', encoding='utf-8')
                second = fashion.review_prompt('prompt')
                self.assertIn('第二版规范', fashion.rules_instruction())
                self.assertNotEqual(first['rules_sha256'], second['rules_sha256'])
                self.assertEqual(second['rules_text'], '第二版规范')
                self.assertEqual(first['prompt_sha256'], second['prompt_sha256'])

    def test_missing_or_empty_rules_do_not_fall_back_to_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'rules.md'
            with patch.object(fashion, 'RULES_PATH', source), patch.object(fashion, 'RULES_DIR', source.parent):
                with self.assertRaises(FileNotFoundError):
                    fashion.rules_instruction()
                source.write_text(' \n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'empty'):
                    fashion.rules_instruction()

    def test_complete_structure_allows_three_shots_but_requires_semantic_review(self):
        result = fashion.review_prompt(sample_prompt())
        self.assertEqual(result['structure_warnings'], [])
        self.assertEqual(result['english_word_count'], 4)
        self.assertTrue(result['semantic_review_required'])

    def test_cli_checks_a_saved_prompt_with_chinese_section_numbers(self):
        prompt = sample_prompt()
        for label, number in fashion.CHINESE_NUMBERS.items():
            prompt = prompt.replace(f'## {number}、', f'## {label}、')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'prompt.txt'
            path.write_text(prompt, encoding='utf-8')
            result = subprocess.run([sys.executable, '-X', 'utf8', fashion.__file__, 'check', '--prompt', str(path)],
                                    capture_output=True, text=True, encoding='utf-8', check=True)
        self.assertIn('"structure_warnings": []', result.stdout)

    def test_missing_section_and_translation_in_shots_are_reported(self):
        prompt = sample_prompt().replace('## 8、完整中文参考\n具体内容。', '')
        prompt = prompt.replace('## 6、三分镜完整脚本\n具体内容。', '## 6、三分镜完整脚本\n中文参考：看看领口！')
        warnings = fashion.review_prompt(prompt)['structure_warnings']
        self.assertTrue(any('第8部分' in item for item in warnings))
        self.assertTrue(any('第6部分' in item for item in warnings))

    def test_independent_markdown_needs_no_registration_or_fashion_sections(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            rules = '# 开箱视频\n只使用中文，无需英文口播。\n\n## 输出结构\n1. 开箱过程\n2. 使用感受\n'
            source = directory / '开箱规则.md'
            source.write_text(rules, encoding='utf-8')
            with patch.object(fashion, 'RULES_DIR', directory):
                selected = fashion.select_rules_file('规则文件：开箱规则.md\n生成一个视频')
                instruction = fashion.rules_instruction(selected)
                result = fashion.review_prompt('## 一、开箱过程\n打开包裹。\n## 二、使用感受\n中文介绍。', rules_file=selected)
                self.assertEqual(selected, '开箱规则.md')
                self.assertIn(rules.strip(), instruction)
                self.assertNotIn('欧美大码女装', instruction)
                self.assertEqual(result['structure_warnings'], [])
                self.assertEqual(result['rules_file'], selected)
                source.write_text('# 自由结构\n只写三句话。', encoding='utf-8')
                self.assertIn('只写三句话', fashion.rules_instruction(selected))

    def test_missing_selected_document_does_not_use_default_rules(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(fashion, 'RULES_DIR', Path(temp)):
            with self.assertRaises(FileNotFoundError):
                fashion.select_rules_file('规则文件：missing.md')
            with self.assertRaises(ValueError):
                fashion.resolve_rules('../outside.md')
            with self.assertRaises(ValueError):
                fashion.resolve_rules('config.json')

    def test_duration_changes_speech_budget_without_rewriting_prompt(self):
        prompt = sample_prompt().replace('Look at this neckline!', ' '.join(['word'] * 40))
        short = fashion.review_prompt(prompt, 15)
        long = fashion.review_prompt(prompt, 20)
        self.assertTrue(any('预算' in item for item in short['structure_warnings']))
        self.assertEqual(long['structure_warnings'], [])
        self.assertEqual(short['prompt_sha256'], long['prompt_sha256'])


if __name__ == '__main__':
    unittest.main()
