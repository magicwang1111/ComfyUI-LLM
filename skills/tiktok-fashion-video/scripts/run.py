import argparse
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import requests

RUN = Path(__file__).resolve().parent
BASE = os.environ.get('COMFY_BASE_URL', 'http://127.0.0.1:18183')

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
    session = requests.Session()
    response = session.post(BASE + '/login', data={'username': os.environ['COMFY_USERNAME'], 'password': os.environ['COMFY_PASSWORD']}, timeout=30)
    response.raise_for_status()
    assert session.cookies.get('jwt_token'), 'No jwt_token login cookie'
    return session

def submit(args):
    assert not (RUN / 'submission-intent.json').exists(), 'Intent exists. Never automatically resubmit; poll/reconcile existing job.'
    s = login()
    assert args.workflow and args.face and args.garment and args.prompt and args.pid, 'Submit requires workflow, face, garment, prompt, PID'
    assert len(args.pid)==19 and args.pid.isdecimal(), 'PID must be an exact 19-digit string'
    workflow = json.loads(args.workflow.read_text(encoding='utf-8'))
    for node, path in [('79', args.face), ('78', args.garment)]:
        with path.open('rb') as f:
            r = s.post(BASE + '/upload/image', files={'image': (f'tiktok-{args.pid}-{node}.jpg', f, 'image/jpeg')}, data={'type':'input', 'overwrite':'false'}, timeout=90)
        r.raise_for_status()
        info = r.json()
        workflow[node]['inputs']['image'] = (info.get('subfolder','') + '/' + info['name']).lstrip('/')
    workflow['61']['inputs'].update(prompt=args.prompt.read_text(encoding='utf-8'), duration=args.duration, model_version=args.model, resolution='720P', aspect_ratio='9:16', audio_generation='Enabled', enhance_prompt='Disabled')
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
    response = r.json()
    save('submission-response.json', response)
    if r.status_code != 200 or not response.get('prompt_id'):
        status('submission_rejected', errors=[{'status':r.status_code, 'response_file':'submission-response.json'}])
        print('Submission rejected; inspect saved response. No retry.')
        return
    save('job.json', {'prompt_id':response['prompt_id'], 'fingerprint':fingerprint})
    status('submitted', prompt_id=response['prompt_id'], artifacts={'crop':str(args.garment), 'prompt':str(args.prompt), 'workflow':str(RUN/'workflow-rendered.json')})
    print(json.dumps({'prompt_id':response['prompt_id'], 'stage':'submitted'}))

def poll(args=None):
    job = json.loads((RUN/'job.json').read_text())
    s = login()
    r = s.get(BASE + '/history/' + job['prompt_id'], timeout=60)
    r.raise_for_status()
    data = r.json()
    if job['prompt_id'] in data:
        entry = data[job['prompt_id']]
        save('history.json', entry)
        state = entry.get('status',{})
        status('generation_complete' if state.get('completed') else 'generation_failed' if state.get('status_str') == 'error' else 'running', generation_status=state)
        print(json.dumps({'status':state, 'outputs':entry.get('outputs',{})}, ensure_ascii=False))
    else:
        status('running')
        print('Job pending/running; no completed history yet.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['submit','poll'])
    parser.add_argument('--run-dir',type=Path,default=RUN)
    parser.add_argument('--base-url',default=BASE)
    parser.add_argument('--workflow',type=Path)
    parser.add_argument('--face',type=Path)
    parser.add_argument('--garment',type=Path)
    parser.add_argument('--prompt',type=Path)
    parser.add_argument('--pid')
    parser.add_argument('--duration',type=int,default=15)
    parser.add_argument('--model',default='3.0-prime')
    args = parser.parse_args()
    RUN=args.run_dir.resolve()
    RUN.mkdir(parents=True,exist_ok=True)
    BASE=args.base_url.rstrip('/')
    {'submit':submit, 'poll':poll}[args.action](args)
