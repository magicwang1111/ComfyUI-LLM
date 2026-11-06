import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "tiktok_run", Path(__file__).resolve().parents[1] / "skills/tiktok-fashion-video/scripts/run.py"
)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class TikTokRuntimeTests(unittest.TestCase):
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
