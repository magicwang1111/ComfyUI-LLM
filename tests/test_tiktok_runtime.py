import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PIL import Image


spec = importlib.util.spec_from_file_location(
    "tiktok_run", Path(__file__).resolve().parents[1] / "skills/tiktok-fashion-video/scripts/run.py"
)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
collector_spec = importlib.util.spec_from_file_location('tiktok_collect', Path(spec.origin).with_name('collect_product.py'))
collector = importlib.util.module_from_spec(collector_spec)
collector_spec.loader.exec_module(collector)


class TikTokRuntimeTests(unittest.TestCase):
    def test_browser_paths_are_relative_to_the_node_after_migration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            config = collector.browser_config(root)
            self.assertEqual(config['profile_dir'], str(root / '.tiktok_browser/profile'))
            self.assertEqual(config['playwright_module'], str(root / '.tiktok_browser/node_modules/playwright'))
            (root / 'config.local.json').write_text(json.dumps({'tiktok_browser': {'profile_dir': 'migrated/profile'}}), encoding='utf-8')
            self.assertEqual(collector.browser_config(root)['profile_dir'], str(root / 'migrated/profile'))

    def test_collection_preserves_exact_pid_and_verifies_cached_photos(self):
        pid = '1731259010175242313'
        buffer = io.BytesIO()
        Image.new('RGB', (80, 100), 'green').save(buffer, format='JPEG')
        product = {'pid': pid, 'title': 'Verified dress', 'url': f'https://seller.us.tiktokshopglobalselling.com/product/edit/{pid}',
                   'images': [{'url': 'https://p16.ttcdn-us.com/photo.jpg'}]}
        response = SimpleNamespace(content=buffer.getvalue(), raise_for_status=lambda: None)
        with tempfile.TemporaryDirectory() as temp, patch.object(collector, 'read_product', return_value=product) as browser, patch.object(collector.requests, 'get', return_value=response):
            directory = Path(temp)
            output = directory / 'contact.jpg'
            result = collector.collect(pid, directory, output)
            self.assertEqual(result['pid'], pid)
            self.assertEqual(result['images'][0]['size'], [80, 100])
            self.assertTrue(output.is_file())
            collector.collect(pid, directory, output)
            browser.assert_called_once()
            with self.assertRaisesRegex(ValueError, 'PID'):
                collector.collect('1731259010175242314', directory, output)
            Path(result['images'][0]['path']).write_bytes(b'corrupted')
            with self.assertRaises(ValueError):
                collector.collect(pid, directory, output)

    def test_invalid_pid_and_non_product_urls_do_not_access_network(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(collector, 'read_product') as browser, patch.object(collector.requests, 'get') as get:
            with self.assertRaises(ValueError):
                collector.collect('1731259010175240000.0', temp, Path(temp) / 'contact.jpg')
            with self.assertRaises(ValueError):
                collector.download_image((1, {'url': 'http://127.0.0.1:8188/private'}, Path(temp)))
            browser.assert_not_called()
            get.assert_not_called()

    def test_prepare_uses_bundled_workflow_and_agent_written_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'product').mkdir()
            (directory / 'product/manifest.json').write_text(json.dumps({'pid': '1731259010175242313', 'title': 'Verified dress', 'source_url': 'https://example.com/product'}), encoding='utf-8')
            args = SimpleNamespace(pid='1731259010175242313', prompt_text='Complete new product prompt', duration=15, model='3.0-prime', execution_notes='核验：商品标题匹配。\n去重范围：仅本商品历史。', caption_text='Little details 💚', hashtags=['#OutfitInspo', '#CasualStyle'])
            original = run.WORKFLOW_TEMPLATE.read_bytes()
            with patch.object(run, 'RUN', directory), patch.object(run, 'login') as login:
                run.prepare(args)
                rendered = json.loads((directory / 'workflow.json').read_text(encoding='utf-8'))
                self.assertEqual(rendered['61']['inputs']['prompt'], args.prompt_text)
                self.assertEqual(rendered['61']['inputs']['duration'], 15)
                self.assertEqual(rendered['79']['inputs']['image'], '')
                self.assertEqual((directory / 'prompt.txt').read_text(encoding='utf-8'), args.prompt_text)
                notes_path = directory / 'execution-notes.md'
                self.assertEqual(notes_path.read_text(encoding='utf-8'), args.execution_notes)
                self.assertNotIn(args.execution_notes, json.dumps(rendered, ensure_ascii=False))
                posting = json.loads((directory / 'post-copy.json').read_text(encoding='utf-8'))
                self.assertEqual(posting['caption_english'], args.caption_text)
                self.assertEqual(posting['hashtags'], args.hashtags)
                self.assertEqual(posting['rules_file'], run.POST_COPY_RULES_PATH.name)
                self.assertNotIn(args.caption_text, json.dumps(rendered, ensure_ascii=False))
                review = json.loads((directory / 'prompt-review.json').read_text(encoding='utf-8'))
                self.assertTrue(review['structure_warnings'])
                self.assertTrue(review['semantic_review_required'])
                self.assertEqual(review['prompt_sha256'], run.hashlib.sha256(args.prompt_text.encode()).hexdigest())
                self.assertIn('完整要求总结', review['rules_text'])
                args.execution_notes = None
                run.prepare(args)
                self.assertIn('去重范围：仅本商品历史。', notes_path.read_text(encoding='utf-8'))
                args.execution_notes = '复核：已更新可用历史范围。'
                run.prepare(args)
                self.assertEqual(notes_path.read_text(encoding='utf-8'), args.execution_notes)
                (directory / 'submission-intent.json').write_text('{}')
                with self.assertRaisesRegex(ValueError, 'intent'):
                    run.prepare(args)
                login.assert_not_called()
            self.assertEqual(run.WORKFLOW_TEMPLATE.read_bytes(), original)

    def test_duration_survives_prepare_and_submit(self):
        for selected, override, expected in ((None, None, 15), (12, None, 12), (20, None, 20), (-1, None, -1), (15, 20, 20)):
            with self.subTest(selected=selected, override=override), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                (directory / 'product').mkdir()
                pid = '1731259010175242313'
                (directory / 'product/manifest.json').write_text(json.dumps({'pid': pid, 'title': 'Dress', 'source_url': 'https://example.com/product'}), encoding='utf-8')
                args = SimpleNamespace(pid=pid, prompt_text='Prompt with selected timing', duration=selected, model='3.0-prime', execution_notes='Private operational notes, not video directions',
                                       workflow=directory / 'workflow.json', prompt=directory / 'prompt.txt',
                                       face=directory / 'face.jpg', garment=directory / 'garment.jpg')
                args.face.write_bytes(b'face')
                args.garment.write_bytes(b'garment')
                session = Mock()
                session.post.return_value.json.side_effect = [{'name': 'face.jpg'}, {'name': 'garment.jpg'}, {'prompt_id': 'test-job'}]
                session.post.return_value.status_code = 200
                with patch.object(run, 'RUN', directory), patch.object(run, 'login', return_value=session):
                    run.prepare(args)
                    prepared = json.loads(args.workflow.read_text(encoding='utf-8'))
                    prepared_duration = 15 if selected is None else selected
                    self.assertEqual(prepared['61']['inputs']['duration'], prepared_duration)
                    self.assertEqual(json.loads((directory / 'prompt-review.json').read_text(encoding='utf-8'))['duration'], prepared_duration)
                    session.get.return_value.json.return_value = {node['class_type']: {'input': {'required': {}}} for node in prepared.values()}
                    args.duration = override
                    run.submit(args)
                submitted = session.post.call_args.kwargs['json']['prompt']
                self.assertEqual(submitted['61']['inputs']['prompt'], args.prompt_text)
                self.assertNotIn(args.execution_notes, json.dumps(submitted))
                self.assertEqual(submitted['61']['inputs']['duration'], expected)
                self.assertEqual(json.loads((directory / 'workflow-rendered.json').read_text(encoding='utf-8'))['61']['inputs']['duration'], expected)
                self.assertEqual(json.loads((directory / 'prompt-submit-review.json').read_text(encoding='utf-8'))['duration'], expected)

    def test_submit_reviews_actual_prompt_before_network_and_preserves_prepare_review(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            args = SimpleNamespace(pid='1731259010175242313', duration=15)
            for name in ('workflow', 'face', 'garment', 'prompt'):
                path = directory / name
                path.write_text('{}' if name == 'workflow' else 'Actual submitted prompt', encoding='utf-8')
                setattr(args, name, path)
            prepared = {'rules_sha256': 'older-specification'}
            (directory / 'prompt-review.json').write_text(json.dumps(prepared), encoding='utf-8')
            with patch.object(run, 'RUN', directory), patch.object(run, 'login', side_effect=RuntimeError('network intentionally stopped')):
                with self.assertRaisesRegex(RuntimeError, 'intentionally stopped'):
                    run.submit(args)
            report = json.loads((directory / 'prompt-submit-review.json').read_text(encoding='utf-8'))
            self.assertEqual(report['prompt_sha256'], run.hashlib.sha256(b'Actual submitted prompt').hexdigest())
            self.assertTrue(any('changed after prepare' in warning for warning in report['structure_warnings']))
            self.assertEqual(json.loads((directory / 'prompt-review.json').read_text(encoding='utf-8')), prepared)
            self.assertFalse((directory / 'submission-intent.json').exists())

    def test_poll_waits_for_existing_job_without_resubmission(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'job.json').write_text(json.dumps({'prompt_id': 'existing-job'}))
            with patch.object(run, 'RUN', directory), patch.object(run, 'login'), patch.object(run, 'poll_once', side_effect=[False, True]) as poll, patch.object(run.time, 'sleep') as sleep:
                run.poll(SimpleNamespace(wait_seconds=120))
                self.assertEqual(poll.call_count, 2)
                sleep.assert_called_once()

    def test_submit_inherits_prepared_markdown_and_rejects_switching_files(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'alternate.md').write_text('# Other rules\nOnly write Chinese.', encoding='utf-8')
            (directory / 'different.md').write_text('# Different rules', encoding='utf-8')
            args = SimpleNamespace(pid='1731259010175242313', duration=15, rules_file=None)
            for name in ('workflow', 'face', 'garment', 'prompt'):
                path = directory / name
                path.write_text('{}' if name == 'workflow' else 'Saved prompt', encoding='utf-8')
                setattr(args, name, path)
            (directory / 'prompt-review.json').write_text(json.dumps({'rules_file': 'alternate.md', 'rules_sha256': 'old'}), encoding='utf-8')
            rules_module = importlib.import_module('fashion_prompt')
            with patch.object(run, 'RUN', directory), patch.object(rules_module, 'RULES_DIR', directory):
                with patch.object(run, 'login', side_effect=RuntimeError('stop before network')):
                    with self.assertRaisesRegex(RuntimeError, 'stop before network'):
                        run.submit(args)
                review = json.loads((directory / 'prompt-submit-review.json').read_text(encoding='utf-8'))
                self.assertEqual(review['rules_file'], 'alternate.md')
                self.assertIn('Only write Chinese.', review['rules_text'])
                args.rules_file = 'different.md'
                with patch.object(run, 'login') as login:
                    with self.assertRaisesRegex(ValueError, 'differs from prepare'):
                        run.submit(args)
                    login.assert_not_called()

    def test_task_session_uses_bearer_without_password_login(self):
        env = {"COMFY_TASK_TOKEN": "alice-token", "COMFY_TASK_BASE_URL": "http://127.0.0.1:8183"}
        with patch.dict(run.os.environ, env, clear=True), patch.object(run, "BASE", env["COMFY_TASK_BASE_URL"]), patch.object(run.requests.Session, "post") as post:
            self.assertEqual(run.login().headers['Authorization'], 'Bearer alice-token')
            post.assert_not_called()

    def test_task_token_cannot_be_sent_to_another_endpoint(self):
        with patch.dict(run.os.environ, {"COMFY_TASK_TOKEN": "token", "COMFY_TASK_BASE_URL": "http://127.0.0.1:8183"}, clear=True), patch.object(run, "BASE", "https://other.example"), patch.object(run.requests, "Session") as session:
            with self.assertRaisesRegex(ValueError, 'current ComfyUI instance'):
                run.login()
            session.assert_not_called()

    def test_missing_task_identity_does_not_use_shared_credentials(self):
        env = {"COMFY_TASK_AUTH_ERROR": "Missing task owner", "COMFY_USERNAME": "shared", "COMFY_PASSWORD": "secret"}
        with patch.dict(run.os.environ, env, clear=True), patch.object(run.requests, "Session") as session:
            with self.assertRaisesRegex(ValueError, 'Missing task owner'):
                run.login()
            session.assert_not_called()

    def test_missing_credentials_are_reported_before_network_access(self):
        with patch.dict(run.os.environ, {}, clear=True), patch.object(run.requests, "Session") as session:
            with self.assertRaisesRegex(ValueError, "COMFY_USERNAME, COMFY_PASSWORD"):
                run.login()
            session.assert_not_called()

    def test_missing_submission_files_are_reported_before_login(self):
        with tempfile.TemporaryDirectory() as temp:
            args = SimpleNamespace(
                workflow=Path(temp) / "missing.json", face=Path(temp) / "face.png",
                garment=Path(temp) / "garment.png", prompt=Path(temp) / "prompt.txt",
                pid="1731259010175242313",
            )
            with patch.object(run, "RUN", Path(temp)), patch.object(run, "login") as login:
                with self.assertRaisesRegex(ValueError, "Missing workflow file"):
                    run.submit(args)
                login.assert_not_called()
                self.assertFalse((Path(temp) / "submission-intent.json").exists())


if __name__ == "__main__":
    unittest.main()
