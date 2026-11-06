import argparse
import base64
import json
import os
import io
import time
from pathlib import Path
import requests
from PIL import Image, ImageOps
from video_media import compress_for_qc

MAX_INLINE_BYTES = 12 * 1024 * 1024
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def make_payload(instruction, video, face, garment, small=False):
    parts = [{'text': instruction}]
    parts.append({'inlineData': {'mimeType': 'video/mp4', 'data': base64.b64encode(video.read_bytes()).decode()}})
    for path in (face, garment):
        with Image.open(path) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
            edge = 960 if small else 1280
            image.thumbnail((edge, edge))
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
        parts.append({'inlineData': {'mimeType': 'image/jpeg', 'data': base64.b64encode(buffer.getvalue()).decode()}})
    return json.dumps({'contents': [{'role': 'user', 'parts': parts}],
                       'generationConfig': {'temperature': 0.1, 'responseMimeType': 'application/json'}}, ensure_ascii=False).encode('utf-8')


def request_qc(args, key, instruction):
    video = args.video
    small = False
    payload = make_payload(instruction, video, args.face, args.garment)
    if len(payload) > MAX_INLINE_BYTES:
        video = compress_for_qc(args.video, args.output.with_name('qc-video.mp4'))
        payload = make_payload(instruction, video, args.face, args.garment)
    if len(payload) > MAX_INLINE_BYTES:
        small = True
        video = compress_for_qc(args.video, args.output.with_name('qc-video-small.mp4'), small=True)
        payload = make_payload(instruction, video, args.face, args.garment, small=True)
    attempts = []
    # At most three HTTP attempts total, including the smaller-payload 413 retry.
    for attempt in range(3):
        if len(payload) > MAX_INLINE_BYTES:
            raise ValueError('QC request remains too large after compression; original video is preserved.')
        info = {'attempt': attempt + 1, 'request_bytes': len(payload), 'video': str(video),
                'compressed': video != args.video}
        response = None
        try:
            response = requests.post(f'{args.base_url}/models/{args.model}:generateContent',
                                     headers={'x-goog-api-key': key, 'Content-Type': 'application/json'},
                                     data=payload, timeout=(30, 180))
            info['status'] = response.status_code
        except (requests.Timeout, requests.ConnectionError) as exc:
            info['error'] = type(exc).__name__
        attempts.append(info)
        args.output.with_suffix('.attempts.json').write_text(json.dumps(attempts, indent=2), encoding='utf-8')
        if response is not None and response.status_code == 200:
            return response.json()
        if response is not None and response.status_code == 413 and not small and attempt < 2:
            small = True
            video = compress_for_qc(args.video, args.output.with_name('qc-video-small.mp4'), small=True)
            smaller = make_payload(instruction, video, args.face, args.garment, small=True)
            if len(smaller) >= len(payload):
                break
            payload = smaller
            print('Gemini HTTP 413: retrying with a smaller full-length video/audio copy.', flush=True)
            continue
        if response is not None and response.status_code not in RETRYABLE_STATUS:
            break
        if attempt == 2:
            break
        delay = 2 ** (attempt + 1)
        if response is not None:
            try:
                delay = max(delay, min(60, float(response.headers.get('Retry-After', 0))))
            except ValueError:
                pass
        print(f'Gemini temporary failure; retry {attempt + 2}/3 after {delay}s.', flush=True)
        time.sleep(delay)
    args.output.with_suffix('.error.json').write_text(json.dumps(attempts[-1]), encoding='utf-8')
    failure = f'HTTP {response.status_code}' if response is not None else attempts[-1]['error']
    raise ValueError(f'Gemini {failure}; stopped after {len(attempts)} attempts. Original video is preserved.')


def save_qc(args, data):
    text = ''.join(p.get('text', '') for p in data['candidates'][0]['content']['parts'])
    parsed = json.loads(text.removeprefix('```json').removesuffix('```').strip())
    args.output.with_name('qc.json').write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'response_file': str(args.output), 'qc': parsed}, ensure_ascii=False))

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
        save_qc(args, json.loads(args.output.read_text(encoding='utf-8')))
        return
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    key = os.environ.get('VAPEUR_API_KEY') or config['VAPEUR_API_KEY']
    instruction = '''分析实际视频的画面和原始音轨，不要根据参考图猜台词。后附图片依次是身份参考、服装参考，仅用于视觉一致性比较。逐字转录所有实际可听英文口播，未知词用[unclear]，分说话者及时间戳，提供逐句中文翻译。识别实际镜头数量/内容，参考服装的颜色、领口、袖型、版型、图案和可见结构是否一致，身份相似度仅评价可见视觉一致性，口型、手指、运动、人物比例是否漂移。明确指出BGM、字幕、Logo、水印、购物UI或其他文字是否出现；是否有未核实材质/价格/促销陈述。不要把图像身份参考未展示的下身比例当已知。根据实际内容生成一条简短自然英语TikTok caption和5个相关英文hashtags，不宣称参考以外卖点。输出纯JSON：transcript_segments数组包含start_s,end_s,speaker,english,chinese；transcript_english；translation_chinese；shots数组；qc对象包含audio_present,bgm_present,subtitles_present,logo_or_watermark_present,shop_ui_present,garment_consistency,identity_consistency,lip_sync,issues数组,overall_pass布尔值；caption_english；hashtags数组；uncertainties数组。只分析真实音视频，勿输出Markdown。'''
    instruction += '视频可能为保留完整时长和音轨的压缩质检副本；细节不足时记录不确定性，不把压缩失真当成原片缺陷。'
    data = request_qc(args, key, instruction)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    save_qc(args, data)

if __name__ == '__main__':
    main()
