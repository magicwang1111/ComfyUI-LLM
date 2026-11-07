import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from fashion_prompt import review_prompt

RUN = Path(__file__).resolve().parent
BASE = os.environ.get('COMFY_TASK_BASE_URL') or os.environ.get('COMFY_BASE_URL', '')
WORKFLOW_TEMPLATE = Path(__file__).resolve().parents[3] / 'workflow/20261104wan3-api.json'

def save(name, value):
    target = RUN / name
    tmp = target.with_suffix(target.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(target)

def status(stage, **fields):
    p = RUN / 'status.json'
    data = json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {'errors': [], 'artifacts': {}, 'prompt_id': None}
    data.update(stage=stage, updated_at=datetime.now(timezone.utc).isoformat(), **fields)
    save('status.json', data)

def login():
    if os.environ.get('COMFY_TASK_AUTH_ERROR'):
        raise ValueError(os.environ['COMFY_TASK_AUTH_ERROR'])
    task_token = os.environ.get('COMFY_TASK_TOKEN')
    if task_token:
        if not BASE or BASE.rstrip('/') != os.environ.get('COMFY_TASK_BASE_URL', '').rstrip('/'):
            raise ValueError('Task credentials can only be used with the current ComfyUI instance URL.')
        session = requests.Session()
        session.headers['Authorization'] = 'Bearer ' + task_token
        return session
    missing = [name for name in ('COMFY_USERNAME', 'COMFY_PASSWORD') if not os.environ.get(name)]
    if missing:
        raise ValueError('Standalone video service login is not configured: ' + ', '.join(missing) + '. Agent Node must receive its current task session from Account Manager.')
    if not BASE:
        raise ValueError('Standalone scripts require --base-url or COMFY_BASE_URL.')
    session = requests.Session()
    response = session.post(BASE + '/login', data={'username': os.environ['COMFY_USERNAME'], 'password': os.environ['COMFY_PASSWORD']}, timeout=30)
    response.raise_for_status()
    assert session.cookies.get('jwt_token'), 'No jwt_token login cookie'
    return session

def prepare(args):
    if (RUN / 'submission-intent.json').exists():
        raise ValueError('Submission intent exists; resume this task instead of changing its prompt.')
    manifest = json.loads((RUN / 'product/manifest.json').read_text(encoding='utf-8'))
    if manifest.get('pid') != args.pid:
        raise ValueError('Prepared product PID does not match the requested PID.')
    if not args.prompt_text or not args.prompt_text.strip():
        raise ValueError('Prepare requires the complete video prompt in --prompt-text.')
    duration = args.duration if args.duration is not None else 15
    notes_path = RUN / 'execution-notes.md'
    if getattr(args, 'execution_notes', None) is not None:
        notes_path.write_text(args.execution_notes, encoding='utf-8')
    report = review_prompt(args.prompt_text, duration, getattr(args, 'rules_file', None))
    save('prompt-review.json', report)
    workflow = json.loads(WORKFLOW_TEMPLATE.read_text(encoding='utf-8'))
    workflow['61']['inputs']['prompt'] = args.prompt_text
    workflow['61']['inputs']['duration'] = duration
    workflow['61']['inputs']['model_version'] = args.model
    workflow['79']['inputs']['image'] = ''
    workflow['78']['inputs']['image'] = ''
    save('workflow.json', workflow)
    (RUN / 'prompt.txt').write_text(args.prompt_text, encoding='utf-8')
    save('analysis.json', {'pid': args.pid, 'title': manifest['title'], 'source_url': manifest['source_url'], 'rules_file': report['rules_file']})
    status('prepared', pid=args.pid)
    print(json.dumps({'stage': 'prepared', 'workflow': str(RUN / 'workflow.json'), 'prompt': str(RUN / 'prompt.txt'), 'execution_notes': str(notes_path) if notes_path.exists() else None, 'review': str(RUN / 'prompt-review.json'), 'structure_warnings': report['structure_warnings'], 'semantic_review_required': True}, ensure_ascii=False))


def submit(args):
    assert not (RUN / 'submission-intent.json').exists(), 'Intent exists. Never automatically resubmit; poll/reconcile existing job.'
    assert args.workflow and args.face and args.garment and args.prompt and args.pid, 'Submit requires workflow, face, garment, prompt, PID'
    assert len(args.pid)==19 and args.pid.isdecimal(), 'PID must be an exact 19-digit string'
    for name in ('workflow', 'face', 'garment', 'prompt'):
        if not getattr(args, name).is_file():
            raise ValueError(f'Missing {name} file: {getattr(args, name)}')
    workflow = json.loads(args.workflow.read_text(encoding='utf-8'))
    prompt_text = args.prompt.read_text(encoding='utf-8-sig')
    if not prompt_text.strip():
        raise ValueError('Submit requires a nonempty video prompt.')
    previous_review = RUN / 'prompt-review.json'
    previous = json.loads(previous_review.read_text(encoding='utf-8')) if previous_review.exists() else {}
    duration = args.duration if args.duration is not None else workflow['61']['inputs']['duration']
    report = review_prompt(prompt_text, duration, getattr(args, 'rules_file', None) or previous.get('rules_file'))
    if previous.get('rules_file') and previous['rules_file'] != report['rules_file']:
        raise ValueError('Rules file differs from prepare; prepare the prompt with the intended rules before submitting.')
    if previous_review.exists():
        if previous['rules_sha256'] != report['rules_sha256']:
            report['structure_warnings'].append('Script rules changed after prepare; review the prompt against the current specification.')
    save('prompt-submit-review.json', report)
    print(json.dumps({'review': str(RUN / 'prompt-submit-review.json'), 'structure_warnings': report['structure_warnings'], 'semantic_review_required': True}, ensure_ascii=False))
    s = login()
    for node, path in [('79', args.face), ('78', args.garment)]:
        with path.open('rb') as f:
            r = s.post(BASE + '/upload/image', files={'image': (f'tiktok-{args.pid}-{node}.jpg', f, 'image/jpeg')}, data={'type':'input', 'overwrite':'false'}, timeout=90)
        r.raise_for_status()
        info = r.json()
        workflow[node]['inputs']['image'] = (info.get('subfolder','') + '/' + info['name']).lstrip('/')
    workflow['61']['inputs'].update(prompt=prompt_text, duration=duration, model_version=args.model, resolution='720P', aspect_ratio='9:16', audio_generation='Enabled', enhance_prompt='Disabled')
    r = s.get(BASE + '/object_info', timeout=60)
    r.raise_for_status()
    schemas = r.json()
    for key, node in workflow.items():
        schema = schemas[node['class_type']]['input']
        required = schema.get('required', {})
        for name, definition in required.items():
            if definition[0] == 'COMFY_AUTOGROW_V3':
                assert any(k.startswith(name + '.') for k in node['inputs'])
                continue
            assert name in node['inputs'], (key, name)
            val = node['inputs'][name]
            if isinstance(definition[0], list) and not isinstance(val, list):
                assert val in definition[0], (key, name, val)
    save('workflow-rendered.json', workflow)
    fingerprint = hashlib.sha256(json.dumps(workflow, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    intent = {'fingerprint':fingerprint, 'client_id':'tiktok-single-' + fingerprint[:16], 'created_at':datetime.now(timezone.utc).isoformat(), 'state':'submission_unknown_until_response', 'workflow':'workflow-rendered.json'}
    with (RUN / 'submission-intent.json').open('x', encoding='utf-8') as f:
        json.dump(intent, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    status('submitting', fingerprint=fingerprint)
    r = s.post(BASE + '/prompt', json={'prompt':workflow, 'client_id':intent['client_id']}, timeout=120)
    if r.status_code != 200:
        status('submission_rejected', errors=[{'status':r.status_code, 'detail':r.text[:500]}])
        raise ValueError(f'Video submission rejected (HTTP {r.status_code}): {r.text[:500]}')
    response = r.json()
    save('submission-response.json', response)
    if not response.get('prompt_id'):
        status('submission_rejected', errors=[{'status':r.status_code, 'response_file':'submission-response.json'}])
        print('Submission rejected; inspect saved response. No retry.')
        return
    save('job.json', {'prompt_id':response['prompt_id'], 'fingerprint':fingerprint})
    status('submitted', prompt_id=response['prompt_id'], artifacts={'crop':str(args.garment), 'prompt':str(args.prompt), 'workflow':str(RUN/'workflow-rendered.json')})
    print(json.dumps({'prompt_id':response['prompt_id'], 'stage':'submitted'}))

def poll(args=None):
    job = json.loads((RUN/'job.json').read_text())
    s = login()
    deadline = time.monotonic() + min(240, max(0, getattr(args, 'wait_seconds', 0)))
    while True:
        if poll_once(s, job) or time.monotonic() >= deadline:
            return
        time.sleep(min(10, max(0, deadline - time.monotonic())))


def poll_once(s, job):
    r = s.get(BASE + '/history/' + job['prompt_id'], timeout=60)
    r.raise_for_status()
    data = r.json()
    if job['prompt_id'] in data:
        entry = data[job['prompt_id']]
        save('history.json', entry)
        state = entry.get('status',{})
        status('generation_complete' if state.get('completed') else 'generation_failed' if state.get('status_str') == 'error' else 'running', generation_status=state)
        print(json.dumps({'status':state, 'outputs':entry.get('outputs',{})}, ensure_ascii=False))
        return bool(state.get('completed') or state.get('status_str') == 'error')
    else:
        status('running')
        print('Job pending/running; no completed history yet.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare','submit','poll'])
    parser.add_argument('--run-dir',type=Path,default=RUN)
    parser.add_argument('--base-url',default=BASE)
    parser.add_argument('--workflow',type=Path)
    parser.add_argument('--face',type=Path)
    parser.add_argument('--garment',type=Path)
    parser.add_argument('--prompt',type=Path)
    parser.add_argument('--prompt-text')
    parser.add_argument('--execution-notes', help='Product verification, crop selection, history scope and review notes; saved separately from the video prompt.')
    parser.add_argument('--rules-file', help='Markdown file inside workflow; submit inherits the prepared rules when omitted.')
    parser.add_argument('--wait-seconds',type=int,default=120)
    parser.add_argument('--pid')
    parser.add_argument('--duration',type=int, help='Output seconds (2-30, or -1 for smart duration); prepare defaults to 15, submit inherits the workflow when omitted.')
    parser.add_argument('--model',default='3.0-prime')
    args = parser.parse_args()
    RUN=args.run_dir.resolve()
    RUN.mkdir(parents=True,exist_ok=True)
    BASE=args.base_url.rstrip('/')
    args.workflow = args.workflow or RUN / 'workflow.json'
    args.prompt = args.prompt or RUN / 'prompt.txt'
    {'prepare':prepare, 'submit':submit, 'poll':poll}[args.action](args)
