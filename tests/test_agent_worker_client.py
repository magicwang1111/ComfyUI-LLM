import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

from _loader import import_module


client_module = import_module("agent_worker_client")


class RuntimePythonTests(unittest.TestCase):
    def test_context_provider_is_called_for_every_task(self):
        owner = ["alice"]
        provider = lambda: {"COMFY_TASK_TOKEN": owner[0]}
        server = SimpleNamespace(PromptServer=SimpleNamespace(instance=SimpleNamespace(account_manager_task_environment=provider)))
        with patch.dict(sys.modules, {"server": server}):
            self.assertEqual(client_module.current_task_environment()["COMFY_TASK_TOKEN"], "alice")
            owner[0] = "bob"
            self.assertEqual(client_module.current_task_environment()["COMFY_TASK_TOKEN"], "bob")

    def test_isolated_runtime_path_is_platform_specific(self):
        root = Path("plugin")

        self.assertEqual(
            client_module._isolated_python_path(root, "nt"),
            root / ".agent_env" / "Scripts" / "python.exe",
        )
        self.assertEqual(
            client_module._isolated_python_path(root, "posix"),
            root / ".agent_env" / "bin" / "python",
        )

    def test_existing_isolated_runtime_is_preferred(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            isolated = Path(temp_dir) / "python"
            isolated.touch()
            with patch.object(client_module, "_isolated_python_path", return_value=isolated):
                client = client_module.AgentWorkerClient({})

        self.assertEqual(client.python, isolated)

    def test_current_python_is_fallback_when_isolated_runtime_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing-python"
            with patch.object(client_module, "_isolated_python_path", return_value=missing):
                client = client_module.AgentWorkerClient({})

        self.assertEqual(client.python, Path(sys.executable))

    def test_configured_python_remains_authoritative(self):
        configured = Path("custom") / "python"
        client = client_module.AgentWorkerClient({"agent_python": str(configured)})

        self.assertEqual(client.python, configured)


class WorkerCredentialTests(unittest.IsolatedAsyncioTestCase):
    async def test_credentials_only_travel_in_child_environment(self):
        async def spawn(*args, **kwargs):
            env = kwargs["env"]
            self.assertEqual(env["COMFY_TASK_TOKEN"], "private-token")
            self.assertNotIn("COMFY_USERNAME", env)
            self.assertNotIn("COMFY_PASSWORD", env)
            self.assertNotIn("COMFY_BASE_URL", env)
            self.assertNotIn("private-token", Path(args[2]).read_text(encoding="utf-8"))
            Path(args[3]).write_text(json.dumps({"text": "private-token"}), encoding="utf-8")
            stdout, stderr = asyncio.StreamReader(), asyncio.StreamReader()
            stdout.feed_eof()
            stderr.feed_eof()
            return SimpleNamespace(stdout=stdout, stderr=stderr, wait=AsyncMock(return_value=0), returncode=0)

        env = {"COMFY_USERNAME": "shared", "COMFY_PASSWORD": "shared-password", "COMFY_BASE_URL": "https://shared.example"}
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, env), patch.object(client_module.asyncio, "create_subprocess_exec", side_effect=spawn):
            client = client_module.AgentWorkerClient({"agent_python": sys.executable})
            result = await client.run({"prompt": "test"}, temp, task_environment={"COMFY_TASK_TOKEN": "private-token"})
            self.assertEqual(result["text"], "<redacted>")
            self.assertEqual(list(Path(temp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
