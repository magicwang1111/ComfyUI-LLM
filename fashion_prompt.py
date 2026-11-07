"""Read an independent video rules Markdown file and review prompt structure locally."""
import argparse
import hashlib
import json
import re
from pathlib import Path


RULES_DIR = Path(__file__).resolve().parent / 'workflow'
RULES_PATH = RULES_DIR / '欧美大码女装_TikTok视频脚本_完整规范.md'
CHINESE_NUMBERS = dict(zip(('一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三'), range(1, 14)))
for number in range(14, 100):
    tens, units = divmod(number, 10)
    CHINESE_NUMBERS[('' if tens == 1 else '一二三四五六七八九'[tens - 1]) + '十' + ('' if units == 0 else '一二三四五六七八九'[units - 1])] = number
HEADING = re.compile(r'^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:第\s*)?(\d+|[一二三四五六七八九十]+)\s*(?:部分\s*[:：、.．]?|[、.．:：）)])\s*(.+?)\s*$', re.M)


def resolve_rules(rules_file=None):
    source = (RULES_DIR / rules_file).resolve() if rules_file else RULES_PATH.resolve()
    if RULES_DIR.resolve() not in source.parents or source.suffix.lower() != '.md':
        raise ValueError('Video rules must be a Markdown file inside the workflow directory.')
    if not source.is_file():
        raise FileNotFoundError(f'Video rules file does not exist: {source}')
    return source


def select_rules_file(prompt):
    matches = re.findall(r'^\s*(?:规则文件|rules_file)\s*[:：=]\s*([^\r\n]+)', prompt, re.M)
    if len(matches) > 1:
        raise ValueError('Specify one video rules file per task.')
    return resolve_rules(matches[0].strip().strip('"\'') if matches else None).relative_to(RULES_DIR.resolve()).as_posix()


def load_rules(rules_file=None):
    source = resolve_rules(rules_file)
    text = source.read_text(encoding='utf-8-sig').strip()
    if not text:
        raise ValueError(f'Video script rules are empty: {source}')
    return text


def rules_instruction(rules_file=None):
    return (f'\n\n当前视频规则文件：{resolve_rules(rules_file).name}。仅使用此文件的规范。'
            '\n以下为当前完整视频脚本规范；本次用户明确要求优先，仅覆盖对应部分。\n' + load_rules(rules_file))


def review_prompt(prompt, duration=15, rules_file=None):
    source = resolve_rules(rules_file)
    rules = load_rules(rules_file)
    structure = re.search(r'^## .*输出结构\s*\n(.*?)(?=^## |\Z)', rules, re.M | re.S)
    expected = re.findall(r'^(\d+)\.[ \t]*([^：:\n]+?)(?:[：:]|$)', structure.group(1), re.M) if structure else []
    warnings = []
    if not expected:
        warnings.append('此规范未识别到编号输出结构，已跳过章节检查；请依据规范全文审核。')
    headings = list(HEADING.finditer(prompt))
    sections = {}
    order = []
    expected_numbers = [int(number) for number, _ in expected]
    for index, match in enumerate(headings):
        label = match.group(1)
        number = int(label) if label.isdecimal() else CHINESE_NUMBERS.get(label)
        order.append(number)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(prompt)
        sections[number] = prompt[match.end():end].strip()
    for number, title in expected:
        if not sections.get(int(number)):
            warnings.append(f'第{number}部分「{title}」缺失或正文为空。')
    if expected_numbers and [number for number in order if number in expected_numbers] != expected_numbers:
        warnings.append('章节顺序或编号不符合完整输出结构；建议使用「## 一、标题」至最后一部分。')
    translation_rule = re.search(r'所有台词中文翻译只放在第(\d+|[一二三四五六七八九十]+)部分', rules)
    if translation_rule:
        label = translation_rule.group(1)
        translation_section = int(label) if label.isdecimal() else CHINESE_NUMBERS.get(label)
        for number, title in expected:
            if '分镜' in title and int(number) != translation_section and re.search(r'中文参考|中文翻译|中文台词', sections.get(int(number), '')):
                warnings.append(f'第{number}部分出现中文台词翻译字段；对白翻译应集中在第{translation_section}部分。')
    speech_section = next((int(number) for number, title in expected if '英文口播' in title), None)
    speech = sections.get(speech_section, '')
    words = len(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)*", speech))
    if speech and not words:
        warnings.append(f'第{speech_section}部分未识别到英文口播。')
    if duration > 0 and words > duration * 2.4:
        warnings.append(f'英文口播约{words}词，超过{duration}秒按每秒2.4词估算的建议预算；需检查自然语速与回应停顿。')
    return {
        'rules_file': source.relative_to(RULES_DIR.resolve()).as_posix(),
        'rules_source': str(source),
        'rules_sha256': hashlib.sha256(rules.encode('utf-8')).hexdigest(),
        'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
        'rules_text': rules,
        'duration': duration,
        'english_word_count': words,
        'structure_warnings': warnings,
        'semantic_review_required': True,
        'limitations': '仅检查可识别的结构与口播预算；不证明Hook、商品事实、历史去重、当次特殊要求或成片合规。特殊格式按当次用户要求人工复核。',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'show', 'check'])
    parser.add_argument('--rules-file', help='Markdown filename or relative path inside workflow; defaults to the existing fashion rules.')
    parser.add_argument('--prompt', type=Path)
    parser.add_argument('--duration', type=int, default=15)
    args = parser.parse_args()
    if args.action == 'list':
        print('\n'.join(path.relative_to(RULES_DIR).as_posix() for path in sorted(RULES_DIR.rglob('*.md'))))
    elif args.action == 'show':
        print(rules_instruction(args.rules_file))
    else:
        if not args.prompt:
            parser.error('check requires --prompt')
        report = review_prompt(args.prompt.read_text(encoding='utf-8-sig'), args.duration, args.rules_file)
        report.pop('rules_text')
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
