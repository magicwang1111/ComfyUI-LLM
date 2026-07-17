import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import uuid4


ROOT_DIR = Path(__file__).resolve().parent
EVENT_PREFIX = "__COMFYUI_LLM_EVENT__"


def _isolated_python_path(root=ROOT_DIR, platform_name=os.name):
    if platform_name == "nt":
        return root / ".agent_env" / "Scripts" / "python.exe"
    return root / ".agent_env" / "bin" / "python"


def _runtime_installer_path(root=ROOT_DIR, platform_name=os.name):
    suffix = "ps1" if platform_name == "nt" else "sh"
    return root / f"install_agent_runtime.{suffix}"


class AgentWorkerClient:
    def __init__(self, config, timeout=600):
        configured = str(config.get("agent_python") or "").strip()
        isolated = _isolated_python_path()
        self.python = Path(configured).expanduser() if configured else (
            isolated if isolated.is_file() else Path(sys.executable)
        )
        self.timeout = max(60, int(timeout))

    def validate(self):
        if not self.python.is_file():
            raise ValueError(
                f"Agent SDK runtime Python was not found at {self.python}. "
                f"Run {_runtime_installer_path()} once or set agent_python "
                "to a valid Python executable."
            )

    async def run(self, job, work_dir, on_event=None):
        self.validate()
        work_dir = Path(work_dir).resolve()
        token = uuid4().hex
        request_path = work_dir / f".agent_request_{token}.json"
        result_path = work_dir / f".agent_result_{token}.json"
        request_path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                str(self.python),
                str(ROOT_DIR / "agent_worker.py"),
                str(request_path),
                str(result_path),
                cwd=str(ROOT_DIR),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_lines = []
            stderr_lines = []

            async def read_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").rstrip()
                    if text.startswith(EVENT_PREFIX):
                        try:
                            event = json.loads(text[len(EVENT_PREFIX) :])
                            if on_event:
                                on_event(event)
                        except Exception:
                            continue
                    else:
                        stdout_lines.append(text)

            async def read_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    stderr_lines.append(line.decode("utf-8", errors="replace").rstrip())

            stdout_task = asyncio.create_task(read_stdout())
            stderr_task = asyncio.create_task(read_stderr())
            try:
                await asyncio.wait_for(process.wait(), timeout=self.timeout * 2)
                await asyncio.gather(stdout_task, stderr_task)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
                raise ValueError("Agent SDK worker exceeded the task timeout.")
            if process.returncode != 0:
                detail = "\n".join(stderr_lines)[-2000:].strip()
                if "No module named 'agents'" in detail:
                    raise ValueError(
                        f"Agent SDK is not installed for {self.python}. Run "
                        f"{_runtime_installer_path()} once or install "
                        "requirements-agent.txt into that Python environment."
                    )
                raise ValueError(f"Agent SDK worker failed ({process.returncode}): {detail}")
            if not result_path.is_file():
                detail = "\n".join(stdout_lines)[-1000:].strip()
                raise ValueError(f"Agent SDK worker did not return a result: {detail}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if result.get("error"):
                raise ValueError(result["error"])
            return result
        finally:
            request_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)
