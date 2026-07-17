import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _loader import import_module


client_module = import_module("agent_worker_client")


class RuntimePythonTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
