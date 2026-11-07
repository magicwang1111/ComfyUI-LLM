import asyncio
import json
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from _loader import import_module


service_module = import_module('orchestration.service')
nodes = import_module('nodes')
worker_module = import_module('agent_worker_client')


class IndependentNodeTests(unittest.IsolatedAsyncioTestCase):
    async def test_submit_saves_inputs_and_returns_without_starting_worker(self):
        captured = []
        def submit(node_id, job):
            captured.append((node_id, job))
            return 'independent-task'
        server = SimpleNamespace(PromptServer=SimpleNamespace(instance=SimpleNamespace(account_manager_submit_agent=submit)))
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(sys.modules, {'server': server}), patch.object(nodes, 'load_config', return_value={}):
                with patch.object(nodes, 'resolve_runtime_config', return_value={'timeout': 600}), \
                        patch.object(nodes, 'resolve_output_dir', return_value=Path(temp)), \
                        patch.object(nodes, 'AgentWorkerClient') as worker:
                    task_id = await nodes.AgentTaskNode().run_agent(
                        prompt='test', agent_model='gpt-6-astra', skill_override='auto', image_model='gpt-image-2',
                        thinking_level='high', output_dir=temp, max_agent_turns=12, publish_to_oss=False,
                        unique_id='node-1', independent=True,
                    )
                    self.assertEqual(task_id, 'independent-task')
                    worker.assert_not_called()
            self.assertTrue(Path(captured[0][1]['job_dir']).is_dir())
            self.assertEqual(captured[0][0], 'node-1')
            self.assertNotIn('COMFY_TASK_TOKEN', captured[0][1])


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_low_memory_pauses_claims_without_losing_queued_jobs(self):
        service = service_module.AgentService('http://127.0.0.1:8180', b'secret', None, 3072)
        service.request = AsyncMock()
        with patch.object(service_module, 'available_memory_mb', return_value=2048), \
                patch.object(service_module.asyncio, 'sleep', side_effect=asyncio.CancelledError):
            with self.assertRaises(asyncio.CancelledError):
                await service.poll()
        service.request.assert_not_called()
        self.assertTrue(service.waiting_for_memory)

    async def test_signed_service_to_manager_and_result_delivery(self):
        manager = Path(__file__).resolve().parents[2] / 'ComfyUI-Account-Manager' / 'utils'
        if not manager.is_dir():
            self.skipTest('Account Manager checkout required for integration test')
        def load(name):
            spec = importlib.util.spec_from_file_location(name, manager / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = load('agent_tasks').AgentTaskStore(root / 'tasks.db')
            signer = load('internal_api').InternalSigner(str(root / 'secret'))
            sessions = SimpleNamespace(users_db=Mock(), jwt_auth=Mock())
            sessions.users_db.get_user.return_value = ('alice', {'username': 'alice'})
            sessions.jwt_auth.create_access_token.return_value = 'private-token'
            routes = load('agent_task_routes').AgentTaskRoutes(store, sessions, signer, None, SimpleNamespace(port=8180))
            app = web.Application()
            app.router.add_post(routes.INTERNAL, routes.internal)
            async with TestClient(TestServer(app)) as server:
                async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
                    service = service_module.AgentService(str(server.make_url('')).rstrip('/'), signer.secret, client)
                    job = {'job_dir': str(root / 'output'), 'output_root': str(root), 'job_id': 'job-one',
                           'publish_to_oss': False, 'skill_override': 'auto', 'identity': {'external_user_id': 'alice'}}
                    Path(job['job_dir']).mkdir()
                    store.create('alice', 'submit-one', job)
                    task = await service.request({'action': 'claim'})
                    raw = {'text': 'Integration completed', 'route': {'skill_name': 'text'}, 'artifacts': []}
                    with patch.object(service_module, 'load_config', return_value={}), \
                            patch.object(service_module, 'resolve_runtime_config', return_value={'timeout': 600}), \
                            patch.object(service_module, 'AgentWorkerClient', return_value=SimpleNamespace(run=AsyncMock(return_value=raw))):
                        await service.execute(task)
                    saved = store.get(task['id'])
                    self.assertEqual(saved['state'], 'completed')
                    self.assertEqual(saved['result']['text'], raw['text'])
                    self.assertTrue((Path(job['job_dir']) / 'state.json').exists())
                    health = await asyncio.start_server(service.health, '127.0.0.1', 0)
                    async with health:
                        port = health.sockets[0].getsockname()[1]
                        response = await client.get(f'http://127.0.0.1:{port}')
                        self.assertEqual(response.json()['status'], 'ok')

    async def test_forbidden_ports_are_rejected_before_any_connection(self):
        for port in range(8180, 8191):
            with self.assertRaisesRegex(ValueError, 'outside'):
                await service_module.serve(SimpleNamespace(port=port))
        self.assertEqual(service_module.parser().parse_args([]).port, 8195)

    async def test_delivery_restart_does_not_invoke_worker(self):
        service = service_module.AgentService('http://127.0.0.1:8180', b'secret', None)
        service.update = AsyncMock(return_value={'state': 'completed'})
        task = {'id': 'one', 'lease': 'lease', 'job': {'job_dir': 'unused'},
                'environment': {'COMFY_TASK_TOKEN': 'private'}, 'checkpoint': {'text': 'saved'}}
        with patch.object(service_module, 'load_config', return_value={}), \
                patch.object(service_module, 'resolve_runtime_config', return_value={'timeout': 600}), \
                patch.object(service_module, 'AgentWorkerClient') as worker, \
                patch.object(service_module, 'deliver', new=AsyncMock(return_value={'text': 'saved'})) as delivery:
            await service.execute(task)
        worker.assert_not_called()
        delivery.assert_awaited_once()
        self.assertEqual(service.update.call_args.kwargs['state'], 'completed')

    async def test_worker_result_is_checkpointed_before_delivery(self):
        service = service_module.AgentService('http://127.0.0.1:8180', b'secret', None)
        service.update = AsyncMock(return_value={'state': 'completed'})
        result = {'text': 'finished', 'route': {}, 'artifacts': []}
        with tempfile.TemporaryDirectory() as temp:
            task = {'id': 'one', 'lease': 'lease', 'job': {'job_dir': temp},
                    'environment': {'COMFY_TASK_TOKEN': 'private'}, 'checkpoint': None}
            with patch.object(service_module, 'load_config', return_value={}), \
                    patch.object(service_module, 'resolve_runtime_config', return_value={'timeout': 600}), \
                    patch.object(service_module, 'AgentWorkerClient', return_value=SimpleNamespace(run=AsyncMock(return_value=result))), \
                    patch.object(service_module, 'deliver', new=AsyncMock(return_value={'text': 'delivered'})):
                await service.execute(task)
            self.assertEqual(json.loads((Path(temp) / 'agent-worker-result.json').read_text()), result)
        self.assertEqual(service.update.call_args_list[0].kwargs['checkpoint'], result)
        self.assertEqual(service.update.call_args_list[-1].kwargs['state'], 'completed')

    async def test_cancelling_worker_stops_real_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'agent_worker.py').write_text('import time\ntime.sleep(60)\n', encoding='utf-8')
            with patch.object(worker_module, 'ROOT_DIR', root):
                worker = worker_module.AgentWorkerClient({'agent_python': sys.executable})
                pending = asyncio.create_task(worker.run({}, root))
                await asyncio.sleep(.3)
                pending.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(pending, timeout=10)
            self.assertEqual([p.name for p in root.iterdir()], ['agent_worker.py'])


if __name__ == '__main__':
    unittest.main()
