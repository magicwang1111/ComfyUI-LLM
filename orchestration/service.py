import argparse
import asyncio
import hashlib
import hmac
import json
import logging
import time
from pathlib import Path

import httpx

from ..agent_worker_client import AgentWorkerClient
from ..artifact_store import safe_error_message
from ..llm import load_config, resolve_runtime_config
from .runner import deliver


ROOT = Path(__file__).resolve().parents[1]
INTERNAL_PATH = '/account-manager/agent-internal'
LOG = logging.getLogger('agent-service')
EVENT_KEYS = {'event', 'message', 'tool', 'count', 'input_count', 'output_count', 'size', 'skill', 'image_name', 'returncode'}


class AgentService:
    def __init__(self, base_url, secret, client, min_available_memory_mb=0):
        self.base_url = base_url.rstrip('/')
        self.secret = secret
        self.client = client
        self.running = set()
        self.last_contact = 0
        self.min_available_memory_mb = min_available_memory_mb
        self.waiting_for_memory = False

    async def request(self, payload):
        body = json.dumps(payload).encode()
        stamp = str(int(time.time()))
        canonical = f'POST\n{INTERNAL_PATH}\n{stamp}\n{hashlib.sha256(body).hexdigest()}'.encode()
        signature = hmac.new(self.secret, canonical, hashlib.sha256).hexdigest()
        response = await self.client.post(self.base_url + INTERNAL_PATH, content=body, headers={
            'Content-Type': 'application/json', 'X-Account-Manager-Timestamp': stamp,
            'X-Account-Manager-Signature': signature,
        })
        response.raise_for_status()
        self.last_contact = time.time()
        return response.json()

    async def update(self, task, **fields):
        return await self.request({'action': 'update', 'id': task['id'], 'lease': task['lease'], **fields})

    async def execute(self, task):
        events = []
        config = load_config()
        runtime_config = resolve_runtime_config()
        job = task['job']
        # Account Manager supplies the URL; use the configured ingress consistently.
        environment = {**task['environment'], 'COMFY_TASK_BASE_URL': self.base_url}
        token = environment['COMFY_TASK_TOKEN']

        def on_event(event):
            safe = {key: value for key, value in event.items() if key in EVENT_KEYS}
            events.append(json.loads(json.dumps(safe).replace(token, '<redacted>')))

        async def work():
            result = task['checkpoint']
            if result is None:
                worker = AgentWorkerClient(config, timeout=min(runtime_config['timeout'], 42000))
                result = await worker.run(job, job['job_dir'], on_event=on_event, task_environment=environment)
                checkpoint = Path(job['job_dir']) / 'agent-worker-result.json'
                temporary = checkpoint.with_suffix('.tmp')
                temporary.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
                temporary.replace(checkpoint)
                await self.update(task, checkpoint=result, state='delivering')
            final = await deliver(job, result, config)
            await self.update(task, state='completed', result=final, events=events[:])
            events.clear()

        work_task = asyncio.create_task(work())
        last_heartbeat = time.monotonic()
        try:
            while not work_task.done():
                done, _ = await asyncio.wait({work_task}, timeout=5)
                if done:
                    break
                pending = events[:]
                try:
                    response = await self.update(task, events=pending)
                    del events[:len(pending)]
                    last_heartbeat = time.monotonic()
                except httpx.HTTPError:
                    if time.monotonic() - last_heartbeat > 60:
                        raise RuntimeError('Account Manager unavailable; stopping Agent before lease expiry')
                    continue
                if response['state'] == 'cancel_requested':
                    work_task.cancel()
                    await asyncio.gather(work_task, return_exceptions=True)
                    await self.update(task, state='cancelled', events=events[:])
                    return
            await work_task
        except asyncio.CancelledError:
            work_task.cancel()
            await asyncio.gather(work_task, return_exceptions=True)
            raise
        except Exception as exc:
            work_task.cancel()
            await asyncio.gather(work_task, return_exceptions=True)
            message = safe_error_message(exc).replace(token, '<redacted>')
            LOG.error('Task %s: %s', task['id'], message)
            try:
                await self.update(task, state='recovery_required', error=message, events=events[:])
            except httpx.HTTPError:
                LOG.error('Task %s: cannot record failure; lease expiry will flag recovery', task['id'])

    async def poll(self):
        try:
            while True:
                try:
                    self.waiting_for_memory = bool(
                        self.min_available_memory_mb
                        and available_memory_mb() < self.min_available_memory_mb
                    )
                    if self.waiting_for_memory:
                        await asyncio.sleep(5)
                        continue
                    task = await self.request({'action': 'claim'})
                    if task:
                        pending = asyncio.create_task(self.execute(task))
                        self.running.add(pending)
                        pending.add_done_callback(self.running.discard)
                        continue
                except (httpx.HTTPError, ValueError) as exc:
                    LOG.warning('Account Manager connection: %s', type(exc).__name__)
                await asyncio.sleep(2)
        finally:
            pending = list(self.running)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    async def health(self, reader, writer):
        try:
            await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'), timeout=5)
            healthy = time.time() - self.last_contact < 30
            state = 'waiting_for_memory' if self.waiting_for_memory else ('ok' if healthy else 'disconnected')
            body = json.dumps({'status': state, 'running': len(self.running),
                               'min_available_memory_mb': self.min_available_memory_mb}).encode()
            status = b'200 OK' if healthy or self.waiting_for_memory else b'503 Service Unavailable'
            writer.write(b'HTTP/1.1 ' + status + b'\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: '
                         + str(len(body)).encode() + b'\r\n\r\n' + body)
            await writer.drain()
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()


def available_memory_mb():
    path = Path('/proc/meminfo')
    if not path.is_file():
        raise ValueError('--min-available-memory-mb requires Linux /proc/meminfo')
    for line in path.read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) / 1024
    raise ValueError('MemAvailable is missing from /proc/meminfo')


def parser():
    result = argparse.ArgumentParser(description='Run Agent orchestration outside ComfyUI workers')
    result.add_argument('--base-url', default='http://127.0.0.1:8180', help='Existing Account Manager ingress')
    result.add_argument('--port', type=int, default=8195, help='Local health endpoint (8180–8190 reserved)')
    result.add_argument('--secret-file', type=Path, default=None)
    result.add_argument('--min-available-memory-mb', type=int, default=0,
                        help='Linux: pause new Agent claims below this available-memory threshold')
    return result


async def serve(args):
    if not 1 <= args.port <= 65535 or 8180 <= args.port <= 8190:
        raise ValueError('Agent service port must be outside 8180–8190 (default: 8195).')
    if not args.base_url.startswith(('http://127.0.0.1:', 'http://localhost:')):
        raise ValueError('This single-machine service requires a loopback Account Manager URL.')
    if args.min_available_memory_mb < 0:
        raise ValueError('Available-memory threshold must not be negative')
    if args.min_available_memory_mb:
        available_memory_mb()
    manager = ROOT.parent / 'ComfyUI-Account-Manager'
    config_path = manager / 'config.json'
    manager_config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    secret_file = args.secret_file or manager / manager_config.get('scheduler_secret_file', 'scheduler_secret.txt')
    secret = secret_file.read_text(encoding='utf-8').strip().encode()
    if not secret:
        raise ValueError('Empty Account Manager scheduler secret')
    async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
        service = AgentService(args.base_url, secret, client, args.min_available_memory_mb)
        # Bind before claiming any task, so an occupied health port fails without starting work.
        server = await asyncio.start_server(service.health, '127.0.0.1', args.port)
        LOG.info('Agent service health: http://127.0.0.1:%s; Account Manager: %s', args.port, args.base_url)
        async with server:
            await service.poll()


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    try:
        asyncio.run(serve(parser().parse_args()))
    except KeyboardInterrupt:
        pass
