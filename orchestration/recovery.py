"""Recover known TikTok video jobs without replaying model calls or submitting prompts."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from ..artifact_store import LocalArtifactStore


SCRIPTS = Path(__file__).resolve().parents[1] / 'skills' / 'tiktok-fashion-video' / 'scripts'


async def recover(job):
    root = Path(job['job_dir']).resolve()
    children = {child['request_key']: child for child in job['children']}
    runs = []
    for intent_file in root.rglob('submission-intent.json'):
        if not intent_file.resolve().is_relative_to(root):
            continue
        intent = json.loads(intent_file.read_text(encoding='utf-8'))
        child = children.get(intent.get('client_id'))
        if child:
            runs.append((intent_file.parent, child))
    if not runs or len(runs) != len(children):
        raise ValueError('无法完整匹配已有视频任务和本地提交记录，请核对产物后处理；未重新生成。')
    store = LocalArtifactStore(job['output_root'], job_id=job['job_id'], job_dir=root, flat_outputs=True)
    python = job.get('script_python') or sys.executable

    async def script(name, *args):
        result = await asyncio.to_thread(subprocess.run, [python, str(SCRIPTS / name), *args],
                                         capture_output=True, text=True, encoding='utf-8', timeout=300)
        if result.returncode:
            raise ValueError(f'视频恢复步骤 {name} 失败：{result.stderr[-1000:]}')

    for directory, child in runs:
        # A server-side UUID was reserved before submission, so a lost response is recoverable.
        job_file = directory / 'job.json'
        if not job_file.exists():
            job_file.write_text(json.dumps({'prompt_id': child['prompt_id']}), encoding='utf-8')
        elif json.loads(job_file.read_text(encoding='utf-8'))['prompt_id'] != child['prompt_id']:
            raise ValueError('本地视频任务 ID 与服务器记录不一致。')
        while True:
            await script('run.py', 'poll', '--run-dir', str(directory), '--wait-seconds', '30')
            history = directory / 'history.json'
            if history.exists():
                state = json.loads(history.read_text(encoding='utf-8')).get('status', {})
                if state.get('status_str') == 'error':
                    raise ValueError('已有视频任务失败；未自动重新提交。')
                if state.get('completed'):
                    break
            await asyncio.sleep(5)
        await script('download_video.py', '--run-dir', str(directory))
        store.add(directory / 'final.mp4')
    return {'status': 'completed', 'route': {'skill_name': 'tiktok-fashion-video'},
            'text': '已恢复已有视频并完成下载。原始脚本和发布文案保持不变。',
            'events': [], 'usage': None, 'artifacts': [r.disk_dict() for r in store.records]}
