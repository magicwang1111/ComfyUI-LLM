import argparse
import base64
import json
import os
from pathlib import Path
import requests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video',type=Path,required=True)
    parser.add_argument('--face',type=Path,required=True)
    parser.add_argument('--garment',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=Path(__file__).resolve().parents[3] / 'config.local.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model',default='gemini-3.8-flash')
    parser.add_argument('--base-url',default='https://api.vapeur.ai/gemini/v1beta')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Existing QC response; inspect it instead of repeating the request.')
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    key = os.environ.get('VAPEUR_API_KEY') or config['VAPEUR_API_KEY']
    instruction = '''分析实际视频的画面和原始音轨，不要根据参考图猜台词。后附图片依次是身份参考、服装参考，仅用于视觉一致性比较。逐字转录所有实际可听英文口播，未知词用[unclear]，分说话者及时间戳，提供逐句中文翻译。识别实际镜头数量/内容，参考服装的颜色、领口、袖型、版型、图案和可见结构是否一致，身份相似度仅评价可见视觉一致性，口型、手指、运动、人物比例是否漂移。明确指出BGM、字幕、Logo、水印、购物UI或其他文字是否出现；是否有未核实材质/价格/促销陈述。不要把图像身份参考未展示的下身比例当已知。根据实际内容生成一条简短自然英语TikTok caption和5个相关英文hashtags，不宣称参考以外卖点。输出纯JSON：transcript_segments数组包含start_s,end_s,speaker,english,chinese；transcript_english；translation_chinese；shots数组；qc对象包含audio_present,bgm_present,subtitles_present,logo_or_watermark_present,shop_ui_present,garment_consistency,identity_consistency,lip_sync,issues数组,overall_pass布尔值；caption_english；hashtags数组；uncertainties数组。只分析真实音视频，勿输出Markdown。'''
    parts = [{'text':instruction}]
    for path, mime in [(args.video,'video/mp4'),(args.face,'image/jpeg'),(args.garment,'image/jpeg')]:
        parts.append({'inlineData':{'mimeType':mime,'data':base64.b64encode(path.read_bytes()).decode()}})
    response = requests.post(f'{args.base_url}/models/{args.model}:generateContent',headers={'x-goog-api-key':key,'Content-Type':'application/json'},json={'contents':[{'role':'user','parts':parts}], 'generationConfig':{'temperature':0.1,'responseMimeType':'application/json'}},timeout=600)
    if response.status_code != 200:
        args.output.with_suffix('.error.json').write_text(json.dumps({'status':response.status_code,'reason':response.reason}),encoding='utf-8')
        raise SystemExit(f'Gemini HTTP {response.status_code}; no automatic retry')
    data = response.json()
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    text = ''.join(p.get('text','') for p in data['candidates'][0]['content']['parts'])
    parsed = json.loads(text.removeprefix('```json').removesuffix('```').strip())
    args.output.with_name('qc.json').write_text(json.dumps(parsed,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'response_file': str(args.output), 'qc': parsed}, ensure_ascii=False))

if __name__ == '__main__':
    main()
