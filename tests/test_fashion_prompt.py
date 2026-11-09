import tempfile
import subprocess
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from _loader import import_module

fashion = import_module('fashion_prompt')


def sample_prompt():
    titles = ['服装判断', '基础设定', '主体与服装', '场景', '镜头与情绪总要求', '三分镜完整脚本',
              '完整英文口播', '完整中文参考', '整体表演要求', '声音规范', '人物、服装与场景一致性',
              'Negative Prompt', '最终执行要求']
    bodies = {
        1: '商品品类：上衣\n颜色与可见设计：圆领长袖\n核心穿衣痛点：遮盖腰腹\n核心卖点：较长衣摆\n真实性限制：不推断成分',
        2: '时长：15秒\n画幅：9:16\n帧率：60fps目标\n画质：真人\n风格：UGC\n结构：完整交流\n分镜：三镜\n视角：第一人称\n人物：博主\n英文口播：美式英语\n音乐：无\n字幕：无\n本次创意重点：出门时发现衣摆',
        3: '### 1. 博主\n外貌与体型：保留参考人物\n参考约束：不继承参考服装\n完整穿搭：上衣与牛仔裤\n人物区分：朋友仅画外音',
        4: '场景环境：门廊\n人物初始位置：门前\n触发事件：朋友叫住博主\n完整故事发展：发现、分享、购买',
        5: '摄影者：朋友\n镜头特征：手持轻微起伏\n情绪原则：惊喜转为分享',
        6: '\n\n'.join(f'### 【分镜{number}——展示】\n时间戳：{index * 5}–{(index + 1) * 5}秒\n英文口播：无对白\n语音调教：保留环境声\n镜头语言：正面中景\n人物动作与表情：博主微笑\n转场：自然衔接' for index, number in enumerate(('一', '二', '三'))),
        7: 'Look at this neckline!',
        9: '情绪曲线：惊讶到开心\n逐人表演：博主微笑，朋友画外惊呼\n对白：承接上句',
        10: '允许的声音：脚步\n声音空间与口型：朋友画外音\n禁止的声音：音乐',
        11: '人物：同一张脸\n服装：圆领长袖和固定衣摆\n环境与道具：同一门廊',
        13: '视频目标：15秒竖屏\n逐镜执行：发现、展示、购买\n人物与表演：惊喜分享\n摄影与声音：手持对话\n禁止事项：文字和音乐',
    }
    return '\n\n'.join(f'## {index}、{title}\n' + bodies.get(index, '具体内容。')
                        for index, title in enumerate(titles, 1))


class FashionPromptTests(unittest.TestCase):
    def test_reference_library_loads_full_text_in_stable_order_and_refreshes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp)
            root = skill / 'references' / 'video-scripts'
            root.mkdir(parents=True)
            (root / '02_试穿.TXT').write_text('完整试穿脚本' * 3000, encoding='utf-8-sig')
            nested = root / '01_连衣裙'
            nested.mkdir()
            first = nested / '开场.md'
            first.write_text('第一版开场', encoding='utf-8')
            for name in ('_使用说明.md', '.隐藏.txt', '图片.pdf'):
                (root / name).write_text('不加载的内容', encoding='utf-8')
            (root / '空文件.txt').write_text(' \n', encoding='utf-8')
            disabled = root / '_停用'
            disabled.mkdir()
            (disabled / '旧脚本.md').write_text('不加载的内容', encoding='utf-8')

            instruction, files = fashion.load_script_references(skill)
            self.assertEqual([item['file'] for item in files], ['01_连衣裙/开场.md', '02_试穿.TXT'])
            self.assertIn('完整试穿脚本' * 3000, instruction)
            self.assertNotIn('不加载的内容', instruction)
            self.assertNotIn('\ufeff', instruction)
            first.write_text('第二版开场', encoding='utf-8')
            updated, new_files = fashion.load_script_references(skill)
            self.assertIn('第二版开场', updated)
            self.assertNotIn('第一版开场', updated)
            self.assertNotEqual(files[0]['sha256'], new_files[0]['sha256'])
            self.assertEqual(files[1], new_files[1])

    def test_empty_reference_library_and_invalid_encoding(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp)
            self.assertEqual(fashion.load_script_references(skill), ('', []))
            root = skill / 'references' / 'video-scripts'
            root.mkdir(parents=True)
            self.assertEqual(fashion.load_script_references(skill), ('', []))
            (root / 'bad.txt').write_bytes(b'\xff\xfe\x00')
            with self.assertRaisesRegex(ValueError, 'UTF-8.*bad.txt'):
                fashion.load_script_references(skill)

    def test_reference_library_rejects_links_outside_library(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp)
            root = skill / 'references' / 'video-scripts'
            root.mkdir(parents=True)
            outside = skill / 'private.txt'
            outside.write_text('not reference material', encoding='utf-8')
            try:
                (root / 'linked.txt').symlink_to(outside)
            except OSError:
                self.skipTest('Symlink creation is unavailable')
            with self.assertRaisesRegex(ValueError, 'outside'):
                fashion.load_script_references(skill)

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
        prompt = prompt.replace('## 6、三分镜完整脚本\n', '## 6、三分镜完整脚本\n中文参考：看看领口！\n')
        warnings = fashion.review_prompt(prompt)['structure_warnings']
        self.assertTrue(any('第8部分' in item for item in warnings))
        self.assertTrue(any('第6部分' in item for item in warnings))

    def test_chapter_groups_must_be_separate_and_each_shot_is_checked(self):
        prompt = sample_prompt().replace('\n核心卖点：', '；核心卖点：')
        prompt = prompt.replace('语音调教：保留环境声', '普通声音描述', 1)
        warnings = fashion.review_prompt(prompt)['structure_warnings']
        self.assertTrue(any('第1部分' in item and '核心卖点' in item for item in warnings))
        self.assertTrue(any('第6部分第1镜' in item and '语音调教' in item for item in warnings))
        self.assertFalse(any('第2镜' in item or '第3镜' in item for item in warnings))

    def test_plain_chinese_chapters_do_not_confuse_numbered_characters(self):
        prompt = sample_prompt()
        for label, number in fashion.CHINESE_NUMBERS.items():
            prompt = prompt.replace(f'## {number}、', f'{label}、')
        prompt = prompt.replace('### ', '')
        self.assertEqual(fashion.review_prompt(prompt)['structure_warnings'], [])

    def test_execution_notes_are_flagged_but_creative_constraints_are_allowed(self):
        clean = sample_prompt() + '\n不展示未知背面，不虚构面料成分。'
        self.assertEqual(fashion.review_prompt(clean)['structure_warnings'], [])
        result = fashion.review_prompt(clean + '\n历史去重范围：数据库查询仅限本PID。')
        self.assertTrue(any('执行记录' in item for item in result['structure_warnings']))

    def test_speaker_labels_do_not_inflate_spoken_word_count(self):
        prompt = sample_prompt().replace('Look at this neckline!', 'Stranger: Look at this neckline!\nBlogger: Yes!')
        self.assertEqual(fashion.review_prompt(prompt)['english_word_count'], 5)

    def test_database_copy_uses_only_script_sections_and_separate_posting_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            english = 'Stranger: Look at this neckline!\nBlogger: Yes!'
            chinese = '朋友：看看这个领口！\n博主：对！'
            for header7, header8, header9 in [('7. 完整英文口播', '8. 完整中文参考', '9. 整体表演要求'),
                                             ('## 七、完整英文口播', '## 八、完整中文参考', '## 九、整体表演要求')]:
                (run / 'prompt.txt').write_text(f'{header7}\n{english}\n\n{header8}\n{chinese}\n\n{header9}\n动作说明', encoding='utf-8-sig')
                (run / 'qc.json').write_text(json.dumps({'transcript_english': 'wrong speech', 'caption_english': 'wrong caption'}))
                (run / 'post-copy.json').write_text(json.dumps({'caption_english': 'A little detail 💚', 'hashtags': ['#OutfitInspo']}), encoding='utf-8')
                self.assertEqual(fashion.read_generation_copy(run), {'english': english, 'chinese': chinese,
                                                                      'caption_english': 'A little detail 💚', 'hashtags': ['#OutfitInspo']})
            (run / 'prompt.txt').unlink()
            (run / 'post-copy.json').unlink()
            self.assertEqual(fashion.read_generation_copy(run), {'english': '', 'chinese': '', 'caption_english': '', 'hashtags': []})

    def test_posting_rule_edits_are_read_on_each_task(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'posting.md'
            with patch.object(fashion, 'POST_COPY_RULES_PATH', source):
                source.write_text('Use one emoji.', encoding='utf-8')
                self.assertIn('Use one emoji.', fashion.post_copy_instruction())
                source.write_text('Use two emojis.', encoding='utf-8')
                self.assertIn('Use two emojis.', fashion.post_copy_instruction())

    def test_field_requirements_are_read_from_the_selected_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'rules.md'
            source.write_text('## 输出结构\n1. 开箱\n\n| 1 | 包装；取出 |\n', encoding='utf-8')
            with patch.object(fashion, 'RULES_DIR', source.parent):
                report = fashion.review_prompt('## 一、开箱\n包装：纸盒\n取出：打开盒盖', rules_file=source.name)
                self.assertEqual(report['structure_warnings'], [])
                report = fashion.review_prompt('## 一、开箱\n打开纸盒', rules_file=source.name)
                self.assertTrue(any('包装、取出' in item for item in report['structure_warnings']))

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
        smart = fashion.review_prompt(prompt, -1)
        self.assertEqual(smart['structure_warnings'], [])
        self.assertEqual(smart['duration'], -1)


if __name__ == '__main__':
    unittest.main()
