import json
import sys
from pathlib import Path

from .agent_worker_client import AgentWorkerClient
from .artifact_store import (
    ArtifactRecord,
    LocalArtifactStore,
    publish_records,
    resolve_input_path,
    resolve_output_dir,
)
from .image_tools import (
    mask_to_pil,
    records_to_preview,
    save_input_images,
    scan_images,
    tensor_to_pil_batch,
)
from .llm import (
    VapeurAPIError,
    build_request,
    create_runtime_client,
    extract_text,
    load_config,
    response_json,
    resolve_runtime_config,
    validate_common,
)
from .models import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_THINKING_LEVEL,
    NODE_CATEGORY,
    NODE_PREFIX,
    THINKING_LEVELS,
    default_model,
    model_names,
)
from .skills_runtime import SkillRegistry


def _api_guidance(exc):
    if exc.status_code in {401, 403}:
        return ValueError(
            f"Vapeur rejected the request with {exc.status_code}. "
            "Check VAPEUR_API_KEY and model access."
        )
    if exc.status_code == 429:
        return ValueError("Vapeur rate limit exceeded (429). Wait and retry.")
    return ValueError(str(exc))


class _BaseLLMNode:
    OUTPUT_NODE = False
    CATEGORY = NODE_CATEGORY
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "response_json")
    PROVIDER = ""
    SUPPORTS_IMAGE = False

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "model": (
                model_names(cls.PROVIDER),
                {"default": default_model(cls.PROVIDER)},
            ),
            "thinking_level": (
                THINKING_LEVELS,
                {"default": DEFAULT_THINKING_LEVEL},
            ),
            "system_prompt": (
                "STRING",
                {"multiline": True, "default": DEFAULT_SYSTEM_PROMPT},
            ),
            "user_prompt": (
                "STRING",
                {"multiline": True, "default": ""},
            ),
        }
        result = {"required": required}
        if cls.SUPPORTS_IMAGE:
            result["optional"] = {"image": ("IMAGE",)}
        return result

    async def generate(
        self,
        model,
        thinking_level=DEFAULT_THINKING_LEVEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt="",
        image=None,
    ):
        validate_common(
            self.PROVIDER,
            model,
            thinking_level,
            system_prompt,
            user_prompt,
            image,
        )
        path, payload = build_request(
            self.PROVIDER,
            model,
            thinking_level,
            system_prompt,
            user_prompt,
            image,
        )
        client = create_runtime_client()
        try:
            try:
                response = await client.generate(self.PROVIDER, path, payload)
            except VapeurAPIError as exc:
                raise _api_guidance(exc) from exc
        finally:
            await client.close()
        return extract_text(self.PROVIDER, response), response_json(response)


class GPTLLMNode(_BaseLLMNode):
    PROVIDER = "gpt"
    SUPPORTS_IMAGE = True


class ClaudeLLMNode(_BaseLLMNode):
    PROVIDER = "claude"
    SUPPORTS_IMAGE = True


class GeminiLLMNode(_BaseLLMNode):
    PROVIDER = "gemini"
    SUPPORTS_IMAGE = True


class DeepSeekLLMNode(_BaseLLMNode):
    PROVIDER = "deepseek"


AGENT_IMAGE_MODELS = ["gpt-image-2"]
AGENT_PROGRESS_EVENT = "comfyui-llm-agent-progress"

SKILL_LABELS = {
    "auto": "自动选择",
    "batch-ai-tryon": "批量AI换装",
    "batch-apparel-detail-pages": "批量服装详情页",
    "batch-clothing-product-images": "批量服装电商主图",
    "batch-clothing-white-bg-images": "批量服装白底图",
    "clothing-display-image-to-image": "服装陈列图生图",
    "fashion-design-analysis": "服装设计分析",
    "hot-style-analyzer": "服装爆款分析",
    "outfit-flatlay-stylist": "服装搭配平铺",
    "print-pattern-derivation": "印花图案衍生",
    "world-buyer": "世界服装买手",
}


def _skill_value(value):
    reverse = {label: name for name, label in SKILL_LABELS.items()}
    return reverse.get(value, value)


def _send_agent_progress(unique_id, event):
    safe_keys = {
        "event",
        "message",
        "tool",
        "count",
        "input_count",
        "output_count",
        "size",
        "skill",
        "image_name",
        "returncode",
    }
    payload = {key: value for key, value in event.items() if key in safe_keys}
    message = str(payload.get("message") or payload.get("event") or "").strip()
    if message:
        event_name = str(payload.get("event") or "status")
        print(f"[ComfyUI-LLM Agent][{event_name}] {message}", flush=True)
    if unique_id is None:
        return
    payload["node_id"] = str(unique_id)
    try:
        from server import PromptServer

        PromptServer.instance.send_sync(AGENT_PROGRESS_EVENT, payload)
    except Exception:
        pass


class AgentSDKNode:
    OUTPUT_NODE = True
    CATEGORY = NODE_CATEGORY
    FUNCTION = "run_agent"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "text")

    @classmethod
    def INPUT_TYPES(cls):
        registry = SkillRegistry()
        skill_options = [SKILL_LABELS.get(name, name) for name in ["auto", *registry.names()]]
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "agent_model": (
                    model_names("gpt"),
                    {"default": default_model("gpt")},
                ),
                "skill_override": (skill_options, {"default": SKILL_LABELS["auto"]}),
                "image_model": (AGENT_IMAGE_MODELS, {"default": "gpt-image-2"}),
                "thinking_level": (
                    [item for item in THINKING_LEVELS if item != "off"],
                    {"default": DEFAULT_THINKING_LEVEL},
                ),
                "output_dir": (
                    "STRING",
                    {"default": "ComfyUI-LLM-Agent"},
                ),
                "max_agent_turns": (
                    "INT",
                    {"default": 12, "min": 1, "max": 50, "step": 1},
                ),
                "publish_to_oss": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "images": ("IMAGE",),
                "mask": ("MASK",),
                "input_path": ("STRING", {"default": ""}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    async def run_agent(
        self,
        prompt,
        agent_model,
        skill_override,
        image_model,
        thinking_level,
        output_dir,
        max_agent_turns,
        publish_to_oss,
        images=None,
        mask=None,
        input_path="",
        unique_id=None,
    ):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt is required.")
        config = load_config()
        runtime_config = resolve_runtime_config()
        root = resolve_output_dir(output_dir, config)
        artifacts = LocalArtifactStore(root, flat_outputs=True)
        _send_agent_progress(unique_id, {"event": "reset", "message": "任务开始"})

        input_paths = save_input_images(images, artifacts.inputs_dir)
        resolved_input = resolve_input_path(input_path, config)
        if resolved_input:
            input_paths.extend(scan_images(resolved_input))
        input_paths = list(dict.fromkeys(Path(path).resolve() for path in input_paths))

        mask_path = None
        batch = tensor_to_pil_batch(images)
        if mask is not None and batch:
            mask_image = mask_to_pil(mask, batch[0].size)
            mask_path = artifacts.inputs_dir / "comfyui_mask.png"
            mask_image.save(mask_path, format="PNG")

        allowed_paths = [artifacts.job_dir]
        if resolved_input:
            allowed_paths.append(resolved_input if resolved_input.is_dir() else resolved_input.parent)
        effective_override = _skill_value(skill_override)
        worker = AgentWorkerClient(config, timeout=runtime_config["timeout"])
        result = await worker.run(
            {
                "prompt": prompt,
                "agent_model": agent_model,
                "skill_override": effective_override,
                "image_model": image_model,
                "thinking_level": thinking_level,
                "max_agent_turns": max_agent_turns,
                "input_paths": [str(path) for path in input_paths],
                "input_path": str(resolved_input or ""),
                "mask_path": str(mask_path) if mask_path else "",
                "allowed_paths": [str(path) for path in allowed_paths],
                "output_root": str(root),
                "job_id": artifacts.job_id,
                "job_dir": str(artifacts.job_dir),
                "flat_outputs": True,
                "script_python": sys.executable,
            },
            artifacts.job_dir,
            on_event=lambda event: _send_agent_progress(unique_id, event),
        )
        route_data = result["route"]
        artifacts.records = [ArtifactRecord(**item) for item in result.get("artifacts", [])]
        publish_config = dict(config)
        publish_config["oss_enabled"] = bool(publish_to_oss and config.get("oss_enabled"))
        await publish_records(artifacts.records, artifacts.job_id, publish_config)
        delivery_mode = "image" if artifacts.records else "text"
        artifact_data = [record.disk_dict() for record in artifacts.records]
        result_state = {
            "job_id": artifacts.job_id,
            "job_dir": str(artifacts.job_dir),
            "status": "completed",
            "delivery_mode": delivery_mode,
            "route": route_data,
            "events": result.get("events", []),
            "artifacts": artifact_data,
        }
        (artifacts.outputs_dir / "artifacts.json").write_text(
            json.dumps(artifact_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (artifacts.outputs_dir / "state.json").write_text(
            json.dumps(result_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return (
            records_to_preview(artifacts.records),
            result["text"],
        )


NODE_CLASS_MAPPINGS = {
    f"{NODE_PREFIX} GPT": GPTLLMNode,
    f"{NODE_PREFIX} Claude": ClaudeLLMNode,
    f"{NODE_PREFIX} Gemini": GeminiLLMNode,
    f"{NODE_PREFIX} DeepSeek": DeepSeekLLMNode,
    f"{NODE_PREFIX} Agent SDK": AgentSDKNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {name: name for name in NODE_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS[f"{NODE_PREFIX} Agent SDK"] = f"{NODE_PREFIX} Agent Node"
