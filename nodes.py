import asyncio
import json
import sys
from pathlib import Path

try:
    from comfy_api.latest import InputImpl, io
except ImportError:  # Allows the lightweight unit-test runtime outside ComfyUI.
    io = None
    InputImpl = None

from .agent_worker_client import AgentWorkerClient, current_task_environment
from .fashion_delivery import current_identity, record_outputs
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
    RETRYABLE_HTTP_STATUS_CODES,
    VapeurAPIError,
    build_request,
    create_runtime_client,
    encode_video,
    estimate_gpt_cost,
    extract_text,
    format_cost_estimate,
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
    VIDEO_SYSTEM_PROMPT,
    default_model,
    model_names,
)
from .skills_runtime import SkillRegistry
from .bailian import (
    BAILIAN_MODELS,
    DEFAULT_BAILIAN_MODEL,
    BailianAPIError,
    extract_bailian_text,
    generate_bailian,
)
from .video_nodes import LLMVideoOutput


def _api_guidance(exc):
    if exc.status_code in RETRYABLE_HTTP_STATUS_CODES:
        return ValueError(
            f"{exc} Vapeur 上游服务暂时不可用，已达到配置的请求次数。"
            "请稍后重试，或选择其他可用模型。"
        )
    if exc.status_code in {401, 403}:
        return ValueError(
            f"{exc} Check VAPEUR_API_KEY, billing, and model access."
        )
    if exc.status_code == 429:
        return ValueError(f"{exc} Check billing/quota or request rate according to the API error above.")
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
        return await self._generate_payload(path, payload)

    async def _generate_payload(self, path, payload):
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

    async def generate(self, *args, **kwargs):
        model = kwargs.get("model")
        if model is None and args:
            model = args[0]
        text, raw = await super().generate(*args, **kwargs)
        estimate = estimate_gpt_cost(model, json.loads(raw))
        return {
            "ui": {"llm_cost": [format_cost_estimate(estimate)]},
            "result": (text, raw),
        }


class ClaudeLLMNode(_BaseLLMNode):
    PROVIDER = "claude"
    SUPPORTS_IMAGE = True


class GeminiLLMNode(_BaseLLMNode):
    PROVIDER = "gemini"
    SUPPORTS_IMAGE = True

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        inputs["optional"]["video"] = ("VIDEO",)
        return inputs

    async def generate(
        self, model, thinking_level=DEFAULT_THINKING_LEVEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT, user_prompt="", image=None, video=None,
    ):
        if video is None:
            return await super().generate(model, thinking_level, system_prompt, user_prompt, image)
        if system_prompt == DEFAULT_SYSTEM_PROMPT:
            system_prompt = VIDEO_SYSTEM_PROMPT
        path, payload = build_request(
            self.PROVIDER, model, thinking_level, system_prompt, user_prompt, image,
        )
        video_b64 = await asyncio.to_thread(encode_video, video)
        payload["contents"][0]["parts"].append(
            {"inlineData": {"mimeType": "video/mp4", "data": video_b64}}
        )
        return await self._generate_payload(path, payload)


class DeepSeekLLMNode(_BaseLLMNode):
    PROVIDER = "deepseek"


class QwenLLMNode(_BaseLLMNode):
    PROVIDER = "qwen"
    SUPPORTS_IMAGE = True

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        del inputs["required"]["thinking_level"]
        return inputs


class BailianQwenNode:
    """Qwen through Alibaba Cloud Model Studio (百炼) directly, with optional video input."""

    CATEGORY = NODE_CATEGORY
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "response_json")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (list(BAILIAN_MODELS), {
                    "default": DEFAULT_BAILIAN_MODEL,
                    "tooltip": "Omni 模型可理解视频音轨（口播）；qwen3.8-max/flash、3.7、3.6 只看画面。",
                }),
                "thinking_level": (THINKING_LEVELS, {"default": "low"}),
                "system_prompt": ("STRING", {"multiline": True, "default": DEFAULT_SYSTEM_PROMPT}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {"image": ("IMAGE",), "video": ("VIDEO",)},
        }

    async def generate(self, model, thinking_level="low", system_prompt=DEFAULT_SYSTEM_PROMPT,
                       user_prompt="", image=None, video=None):
        if video is not None and system_prompt == DEFAULT_SYSTEM_PROMPT:
            system_prompt = VIDEO_SYSTEM_PROMPT
        try:
            response = await generate_bailian(
                model, thinking_level, system_prompt, user_prompt, image, video,
            )
        except BailianAPIError as exc:
            if exc.status_code in {401, 403}:
                raise ValueError(f"{exc} 请检查 BAILIAN_API_KEY、业务空间与模型开通情况。") from exc
            raise ValueError(str(exc)) from exc
        return extract_bailian_text(response), response_json(response)


# Keep the Agent's tool-enabled model list independent of the text node catalog.
AGENT_MODELS = [
    "gpt-6-astra", "gpt-6.1-sol", "gpt-6.1-terra", "gpt-6-sol", "gpt-6-luna",
    "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5", "gpt-5.4", "gpt-5.4-mini",
]
AGENT_IMAGE_MODELS = ["gpt-image-2", "bananapro"]
AGENT_PROGRESS_EVENT = "comfyui-llm-agent-progress"
AGENT_PROGRESS_SAFE_KEYS = {
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


def _sanitize_agent_progress(event):
    return {key: value for key, value in event.items() if key in AGENT_PROGRESS_SAFE_KEYS}


def _send_agent_progress(unique_id, event):
    payload = _sanitize_agent_progress(event)
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


_AgentNodeBase = io.ComfyNode if io is not None else object


class AgentSDKNode(_AgentNodeBase):
    if io is not None:
        @classmethod
        def define_schema(cls):
            registry = SkillRegistry()
            skill_options = [SKILL_LABELS.get(name, name) for name in ["auto", *registry.names()]]
            image_template = io.Autogrow.TemplatePrefix(
                io.Image.Input("image"),
                prefix="image",
                min=1,
                max=16,
            )
            return io.Schema(
                node_id=f"{NODE_PREFIX} Agent SDK",
                display_name=f"{NODE_PREFIX} Agent Node",
                category=NODE_CATEGORY,
                inputs=[
                    io.String.Input("prompt", multiline=True, default=""),
                    io.Combo.Input(
                        "agent_model",
                        options=AGENT_MODELS,
                        default=AGENT_MODELS[0],
                    ),
                    io.Combo.Input(
                        "skill_override",
                        options=skill_options,
                        default=SKILL_LABELS["auto"],
                    ),
                    io.Combo.Input("image_model", options=AGENT_IMAGE_MODELS, default="gpt-image-2"),
                    io.Combo.Input(
                        "thinking_level",
                        options=[item for item in THINKING_LEVELS if item != "off"],
                        default=DEFAULT_THINKING_LEVEL,
                    ),
                    io.String.Input("output_dir", default="ComfyUI-LLM-Agent"),
                    io.Int.Input("max_agent_turns", default=12, min=1, max=50, step=1),
                    io.Boolean.Input("publish_to_oss", default=True),
                    io.Autogrow.Input("reference_images", template=image_template, optional=True),
                    io.Image.Input(
                        "images",
                        optional=True,
                        display_name="images（旧 Batch 兼容）",
                        tooltip="兼容旧工作流；新工作流请使用 image0、image1… 动态输入。",
                    ),
                    io.Mask.Input("mask", optional=True),
                    io.String.Input("input_path", default="", optional=True),
                ],
                outputs=[
                    io.Image.Output(display_name="images"),
                    io.String.Output(display_name="text"),
                    io.Video.Output(display_name="video", is_output_list=True),
                ],
                hidden=[io.Hidden.unique_id],
                is_output_node=True,
            )

        @classmethod
        async def execute(cls, **kwargs):
            node = cls()
            images, text, estimated_cost, agent_progress, videos = await node.run_agent(
                **kwargs,
                unique_id=cls.hidden.unique_id,
            )
            return io.NodeOutput(
                images,
                text,
                videos,
                ui={
                    "llm_cost": [estimated_cost],
                    "agent_progress": agent_progress,
                },
            )
    else:
        OUTPUT_NODE = True
        CATEGORY = NODE_CATEGORY
        FUNCTION = "execute_legacy"
        RETURN_TYPES = ("IMAGE", "STRING", "VIDEO")
        RETURN_NAMES = ("images", "text", "video")
        OUTPUT_IS_LIST = (False, False, True)

        @classmethod
        def INPUT_TYPES(cls):
            registry = SkillRegistry()
            skill_options = [SKILL_LABELS.get(name, name) for name in ["auto", *registry.names()]]
            return {
                "required": {
                    "prompt": ("STRING", {"multiline": True, "default": ""}),
                    "agent_model": (AGENT_MODELS, {"default": AGENT_MODELS[0]}),
                    "skill_override": (skill_options, {"default": SKILL_LABELS["auto"]}),
                    "image_model": (AGENT_IMAGE_MODELS, {"default": "gpt-image-2"}),
                    "thinking_level": (
                        [item for item in THINKING_LEVELS if item != "off"],
                        {"default": DEFAULT_THINKING_LEVEL},
                    ),
                    "output_dir": ("STRING", {"default": "ComfyUI-LLM-Agent"}),
                    "max_agent_turns": ("INT", {"default": 12, "min": 1, "max": 50, "step": 1}),
                    "publish_to_oss": ("BOOLEAN", {"default": True}),
                },
                "optional": {
                    "images": ("IMAGE",),
                    "mask": ("MASK",),
                    "input_path": ("STRING", {"default": ""}),
                },
                "hidden": {"unique_id": "UNIQUE_ID"},
            }

    async def execute_legacy(self, **kwargs):
        images, text, estimated_cost, agent_progress, videos = await self.run_agent(**kwargs)
        return {
            "ui": {
                "llm_cost": [estimated_cost],
                "agent_progress": agent_progress,
            },
            "result": (images, text, videos),
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
        reference_images=None,
        images=None,
        mask=None,
        input_path="",
        unique_id=None,
        independent=False,
    ):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt is required.")
        config = load_config()
        runtime_config = resolve_runtime_config()
        root = resolve_output_dir(output_dir, config)
        artifacts = LocalArtifactStore(root, flat_outputs=True)
        _send_agent_progress(unique_id, {"event": "reset", "message": "任务开始"})

        dynamic_items = list((reference_images or {}).items())
        dynamic_items.sort(
            key=lambda item: (
                int(item[0][5:])
                if item[0].startswith("image") and item[0][5:].isdigit()
                else 999
            )
        )
        dynamic_images = [value for _, value in dynamic_items]
        input_paths = []
        for dynamic_image in dynamic_images:
            input_paths.extend(
                save_input_images(
                    dynamic_image,
                    artifacts.inputs_dir,
                    start_index=len(input_paths) + 1,
                )
            )
        size_reference_path = input_paths[0] if input_paths else None
        input_paths.extend(
            save_input_images(
                images,
                artifacts.inputs_dir,
                start_index=len(input_paths) + 1,
            )
        )
        resolved_input = resolve_input_path(input_path, config)
        if resolved_input:
            input_paths.extend(scan_images(resolved_input))
        input_paths = list(dict.fromkeys(Path(path).resolve() for path in input_paths))

        mask_path = None
        mask_reference = dynamic_images[0] if dynamic_images else images
        batch = tensor_to_pil_batch(mask_reference)
        if mask is not None and batch:
            mask_image = mask_to_pil(mask, batch[0].size)
            mask_path = artifacts.inputs_dir / "comfyui_mask.png"
            mask_image.save(mask_path, format="PNG")

        allowed_paths = [artifacts.job_dir]
        if resolved_input:
            allowed_paths.append(resolved_input if resolved_input.is_dir() else resolved_input.parent)
        effective_override = _skill_value(skill_override)
        ops_identity = None
        if config.get("tiktok_ops", {}).get("enabled"):
            try:
                ops_identity = current_identity()
            except ValueError:
                ops_identity = {}
        job = {
            "prompt": prompt,
            "agent_model": agent_model,
            "skill_override": effective_override,
            "image_model": image_model,
            "thinking_level": thinking_level,
            "max_agent_turns": max_agent_turns,
            "input_paths": [str(path) for path in input_paths],
            "size_reference_path": str(size_reference_path or ""),
            "input_path": str(resolved_input or ""),
            "mask_path": str(mask_path) if mask_path else "",
            "allowed_paths": [str(path) for path in allowed_paths],
            "output_root": str(root),
            "job_id": artifacts.job_id,
            "job_dir": str(artifacts.job_dir),
            "flat_outputs": True,
            "script_python": sys.executable,
        }
        if independent:
            from server import PromptServer

            submit = getattr(PromptServer.instance, "account_manager_submit_agent", None)
            if submit is None:
                raise ValueError("请更新 Account Manager 并启用分布式队列后使用独立 Agent。")
            job["publish_to_oss"] = bool(publish_to_oss)
            return submit(unique_id, job)
        worker = AgentWorkerClient(config, timeout=runtime_config["timeout"])
        result = await worker.run(
            job,
            artifacts.job_dir,
            on_event=lambda event: _send_agent_progress(unique_id, event),
            task_environment=current_task_environment(),
        )
        route_data = result["route"]
        artifacts.records = [ArtifactRecord(**item) for item in result.get("artifacts", [])]
        publish_config = dict(config)
        publish_config["oss_enabled"] = bool(publish_to_oss and config.get("oss_enabled"))
        is_fashion = route_data.get("skill_name") == "tiktok-fashion-video" or effective_override == "tiktok-fashion-video"
        database_enabled = is_fashion and config.get("tiktok_ops", {}).get("enabled", False)
        publishable = [record for record in artifacts.records if not (database_enabled and record.content_type.startswith("video/"))]
        await publish_records(publishable, artifacts.job_id, publish_config)
        database_result = None
        if is_fashion:
            database_result = await record_outputs(artifacts.records, artifacts.job_dir, artifacts.job_id, config, publish_to_oss, ops_identity)
            if database_result:
                messages = [f'视频已保留，等待后台恢复后自动投递：{item["sheet"]}' if item.get('pending')
                            else f'视频已入库：{item["sheet"]} / {item["sequence"]}' for item in database_result['records']]
                messages.extend(database_result['warnings'])
                for message in messages:
                    event = {"event": "database", "message": message}
                    result.setdefault("events", []).append(event)
                    _send_agent_progress(unique_id, event)
                result["text"] += "\n\n" + "\n".join(messages)
        videos = [
            InputImpl.VideoFromFile(record.path)
            for record in artifacts.records
            if record.kind == "output" and record.status == "success"
            and record.content_type.startswith("video/")
        ]
        delivery_mode = "video" if videos else ("image" if artifacts.records else "text")
        artifact_data = [record.disk_dict() for record in artifacts.records]
        result_state = {
            "job_id": artifacts.job_id,
            "job_dir": str(artifacts.job_dir),
            "status": "completed",
            "delivery_mode": delivery_mode,
            "route": route_data,
            "events": result.get("events", []),
            "usage": result.get("usage"),
            "artifacts": artifact_data,
            "database": database_result,
        }
        agent_progress = [
            payload
            for event in result.get("events", [])
            if (payload := _sanitize_agent_progress(event)).get("message")
        ]
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
            format_cost_estimate(result.get("usage"), agent=True),
            agent_progress,
            videos,
        )


class AgentTaskNode(AgentSDKNode):
    """Save inputs and enqueue an Agent without waiting for its final result."""

    if io is not None:
        @classmethod
        def define_schema(cls):
            schema = super().define_schema()
            schema.node_id = f"{NODE_PREFIX} Agent Task"
            schema.display_name = f"{NODE_PREFIX} 独立 Agent 任务"
            for item in schema.inputs:
                if item.id == "reference_images":
                    item.template.min = 0
            schema.outputs = [io.String.Output(display_name="task_id")]
            return schema

        @classmethod
        async def execute(cls, **kwargs):
            task_id = await cls().run_agent(**kwargs, unique_id=cls.hidden.unique_id, independent=True)
            return io.NodeOutput(task_id, ui={"agent_task_id": [task_id]})

        @classmethod
        def fingerprint_inputs(cls, **kwargs):
            return float("nan")
    else:
        RETURN_TYPES = ("STRING",)
        RETURN_NAMES = ("task_id",)
        OUTPUT_IS_LIST = (False,)

        @classmethod
        def IS_CHANGED(cls, **kwargs):
            return float("nan")

        async def execute_legacy(self, **kwargs):
            task_id = await self.run_agent(**kwargs, independent=True)
            return {"ui": {"agent_task_id": [task_id]}, "result": (task_id,)}


NODE_CLASS_MAPPINGS = {
    f"{NODE_PREFIX} GPT": GPTLLMNode,
    f"{NODE_PREFIX} Claude": ClaudeLLMNode,
    f"{NODE_PREFIX} Gemini": GeminiLLMNode,
    f"{NODE_PREFIX} DeepSeek": DeepSeekLLMNode,
    f"{NODE_PREFIX} Qwen": QwenLLMNode,
    f"{NODE_PREFIX} Qwen Bailian": BailianQwenNode,
    f"{NODE_PREFIX} Agent SDK": AgentSDKNode,
    f"{NODE_PREFIX} Agent Task": AgentTaskNode,
    f"{NODE_PREFIX} Video Output": LLMVideoOutput,
}

NODE_DISPLAY_NAME_MAPPINGS = {name: name for name in NODE_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS[f"{NODE_PREFIX} Qwen Bailian"] = f"{NODE_PREFIX} Qwen 百炼"
NODE_DISPLAY_NAME_MAPPINGS[f"{NODE_PREFIX} Agent SDK"] = f"{NODE_PREFIX} Agent Node"
NODE_DISPLAY_NAME_MAPPINGS[f"{NODE_PREFIX} Agent Task"] = f"{NODE_PREFIX} 独立 Agent 任务"
