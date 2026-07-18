import asyncio
import importlib
import json
import sys
import types
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
PACKAGE_NAME = "comfyui_llm_isolated_runtime"
EVENT_PREFIX = "__COMFYUI_LLM_EVENT__"


def _emit(event):
    print(EVENT_PREFIX + json.dumps(event, ensure_ascii=False), flush=True)


def _module(name):
    if PACKAGE_NAME not in sys.modules:
        package = types.ModuleType(PACKAGE_NAME)
        package.__path__ = [str(ROOT_DIR)]
        package.__package__ = PACKAGE_NAME
        sys.modules[PACKAGE_NAME] = package
    return importlib.import_module(f"{PACKAGE_NAME}.{name}")


async def _run(job):
    agent_runtime = _module("agent_runtime")
    artifact_store = _module("artifact_store")
    image_tools = _module("image_tools")
    llm = _module("llm")
    skills_runtime = _module("skills_runtime")

    runtime_config = llm.resolve_runtime_config()
    store = artifact_store.LocalArtifactStore(
        job["output_root"],
        job_id=job["job_id"],
        job_dir=job["job_dir"],
        flat_outputs=bool(job.get("flat_outputs")),
    )
    image_client = image_tools.VapeurImageClient(
        api_key=runtime_config["api_key"],
        timeout=runtime_config["timeout"],
        max_retries=runtime_config["max_retries"],
        retry_delay=runtime_config["retry_delay"],
    )
    runtime = agent_runtime.AgentRuntime(
        registry=skills_runtime.SkillRegistry(),
        artifact_store=store,
        image_client=image_client,
        api_key=runtime_config["api_key"],
        agent_model=job["agent_model"],
        image_model=job["image_model"],
        thinking_level=job["thinking_level"],
        max_turns=job["max_agent_turns"],
        timeout=runtime_config["timeout"],
        allowed_paths=job.get("allowed_paths", []),
        mask_path=job.get("mask_path"),
        size_reference_path=job.get("size_reference_path"),
        script_python=job.get("script_python"),
        event_callback=_emit,
    )
    try:
        input_paths = [Path(item).resolve() for item in job.get("input_paths", [])]
        decision = await runtime.route(
            job["prompt"],
            job["skill_override"],
            input_paths,
            input_path=job.get("input_path", ""),
        )
        route = decision.to_dict()
        if decision.needs_input:
            missing = "；".join(decision.missing_inputs or [decision.reason])
            raise ValueError(f"缺少必要素材：{missing}")
        text = await runtime.execute(job["prompt"], decision, input_paths)
        return {
            "status": "completed",
            "route": route,
            "text": text,
            "events": runtime.events,
            "artifacts": [record.disk_dict() for record in store.records],
        }
    finally:
        await runtime.close()
        await image_client.close()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: agent_worker.py REQUEST_JSON RESULT_JSON")
    request_path = Path(sys.argv[1]).resolve()
    result_path = Path(sys.argv[2]).resolve()
    try:
        job = json.loads(request_path.read_text(encoding="utf-8"))
        result = asyncio.run(_run(job))
    except Exception as exc:
        _emit({"event": "error", "message": f"{type(exc).__name__}: {str(exc)[:1000]}"})
        result = {"error": f"{type(exc).__name__}: {str(exc)[:4000]}"}
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
