import asyncio
import json
import re
import sys
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from agents import (
    Agent,
    ModelSettings,
    OpenAIResponsesModel,
    RunConfig,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from agents.lifecycle import RunHooksBase

from .artifact_store import _is_within
from .image_tools import (
    DEFAULT_IMAGE_MODEL,
    compose_contact_sheet,
    image_data_url,
    save_generated_images,
)
from .skills_runtime import RouteDecision, route_with_rules


set_tracing_disabled(True)


TEXT_ONLY_MARKERS = (
    "只输出文案",
    "只输出文字",
    "只要文案",
    "纯文字",
    "不要生成图片",
    "不生成图片",
    "text only",
    "text-only",
)


def wants_text_only(prompt):
    normalized = str(prompt or "").strip().lower()
    return any(marker in normalized for marker in TEXT_ONLY_MARKERS)


class ReasoningSummaryHooks(RunHooksBase):
    def __init__(self, runtime):
        self.runtime = runtime

    async def on_llm_end(self, context, agent, response):
        for item in response.output:
            if getattr(item, "type", None) != "reasoning":
                continue
            for part in getattr(item, "summary", None) or []:
                summary = str(getattr(part, "text", "") or "").strip()
                if summary:
                    self.runtime._record(
                        "reasoning_summary",
                        f"推理摘要：\n{summary}",
                        agent=agent.name,
                    )


class RouterOutput(BaseModel):
    skill_name: str
    mode: str = "auto"
    confidence: float = Field(ge=0.0, le=1.0)
    input_roles: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    reason: str = ""


class AgentRuntime:
    def __init__(
        self,
        registry,
        artifact_store,
        image_client,
        api_key,
        agent_model="gpt-5.5",
        image_model="auto",
        thinking_level="medium",
        max_turns=12,
        timeout=600,
        allowed_paths=None,
        mask_path=None,
        script_python=None,
        event_callback=None,
    ):
        self.registry = registry
        self.artifact_store = artifact_store
        self.image_client = image_client
        self.agent_model = agent_model
        self.image_model = DEFAULT_IMAGE_MODEL if image_model == "auto" else image_model
        self.thinking_level = thinking_level
        self.max_turns = max(1, min(int(max_turns), 50))
        self.allowed_paths = [Path(item).resolve() for item in (allowed_paths or [])]
        self.mask_path = Path(mask_path).resolve() if mask_path else None
        self.script_python = str(script_python or sys.executable)
        self.events = []
        self.event_callback = event_callback
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.vapeur.ai/v1",
            timeout=float(timeout),
        )
        self.model = OpenAIResponsesModel(model=agent_model, openai_client=self.client)
        self.hooks = ReasoningSummaryHooks(self)

    def _record(self, event, message="", **details):
        payload = {"event": event, **details}
        if message:
            payload["message"] = message
        self.events.append(payload)
        if self.event_callback:
            self.event_callback(payload)
        return payload

    def _settings(self, max_tokens=8192, tool_choice=None):
        return ModelSettings(
            max_tokens=max_tokens,
            reasoning={"effort": self.thinking_level, "summary": "detailed"},
            store=False,
            tool_choice=tool_choice,
        )

    def _input_items(self, text, image_paths):
        content = [{"type": "input_text", "text": text}]
        for path in image_paths[:16]:
            content.append(
                {
                    "type": "input_image",
                    "image_url": image_data_url(path),
                    "detail": "low",
                }
            )
        return [{"role": "user", "content": content}]

    def _remove_rejected_images(self, image_outputs, kept, message):
        kept_ids = {id(item) for item in kept}
        rejected = [item for item in image_outputs if id(item) not in kept_ids]
        for item in rejected:
            Path(item.path).unlink(missing_ok=True)
        image_ids = {id(item) for item in image_outputs}
        non_image_records = [
            item
            for item in self.artifact_store.records
            if id(item) not in image_ids
        ]
        self.artifact_store.records = non_image_records + kept
        if rejected:
            self._record("status", message.format(count=len(rejected)))
        return kept

    @staticmethod
    def _requested_product_image_count(prompt):
        match = re.search(
            r"(?<!\d)(\d{1,2})\s*(?:(?:张|幅)(?:图片|图)?|images?\b)",
            str(prompt or ""),
            flags=re.IGNORECASE,
        )
        return max(1, min(int(match.group(1)), 12)) if match else 3

    @staticmethod
    def _numbered_output_slot(item):
        match = re.match(r"^0*(\d{1,2})(?:[_-]|$)", Path(item.path).stem)
        return int(match.group(1)) if match else None

    @staticmethod
    def _is_named_retry(item):
        return bool(
            re.search(
                r"(?:^|[_\-\s])(?:重做|最终(?:版)?|final|retry|redo|revised|fixed|v\d+)(?:[_\-\s]|$)",
                Path(item.path).stem,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _world_buyer_product_slot(item):
        match = re.search(
            r"world[-_\s]*buyer[-_\s]*product[-_\s]*0*([1-5])(?:\D|$)",
            Path(item.path).stem,
            flags=re.IGNORECASE,
        )
        return int(match.group(1)) if match else None

    @staticmethod
    def _is_world_buyer_contact_sheet(item):
        stem = Path(item.path).stem
        return bool(
            re.search(r"world[-_\s]*buyer.*contact[-_\s]*sheet", stem, re.IGNORECASE)
            or "总览" in stem
        )

    def _replace_named_retries(self, image_outputs):
        latest_by_slot = {}
        retry_slots = set()
        for item in image_outputs:
            slot = self._numbered_output_slot(item)
            if slot is None:
                continue
            if slot in latest_by_slot and self._is_named_retry(item):
                retry_slots.add(slot)
            latest_by_slot[slot] = item
        if not retry_slots:
            return image_outputs

        kept = []
        emitted_retry_slots = set()
        for item in image_outputs:
            slot = self._numbered_output_slot(item)
            if slot not in retry_slots:
                kept.append(item)
            elif slot not in emitted_retry_slots:
                kept.append(latest_by_slot[slot])
                emitted_retry_slots.add(slot)
        kept_slots = [self._numbered_output_slot(item) for item in kept]
        if all(slot is not None for slot in kept_slots) and len(set(kept_slots)) == len(kept):
            kept = [item for _, item in sorted(zip(kept_slots, kept), key=lambda pair: pair[0])]
        return self._remove_rejected_images(
            image_outputs,
            kept,
            "已用复核重做图替换 {count} 张同槽位旧图。",
        )

    @staticmethod
    def _output_by_name(records, image_name):
        requested = Path(str(image_name or "")).name.casefold()
        outputs = [
            item
            for item in records
            if item.kind == "output" and Path(item.path).name.casefold() == requested
        ]
        if len(outputs) != 1:
            available = [
                Path(item.path).name for item in records if item.kind == "output"
            ]
            raise ValueError(
                f"Generated image filename not found: {image_name}. "
                f"Available filenames: {json.dumps(available, ensure_ascii=False)}"
            )
        return outputs[0]

    def _enforce_output_contract(self, skill_name, image_paths, image_outputs, prompt=""):
        image_outputs = self._replace_named_retries(image_outputs)
        if skill_name == "world-buyer":
            latest_by_slot = {}
            contact_sheets = []
            for item in image_outputs:
                slot = self._world_buyer_product_slot(item)
                if slot is not None:
                    latest_by_slot[slot] = item
                elif self._is_world_buyer_contact_sheet(item):
                    contact_sheets.append(item)

            missing_slots = [slot for slot in range(1, 6) if slot not in latest_by_slot]
            if missing_slots or not contact_sheets:
                missing = [f"product-{slot:02d}" for slot in missing_slots]
                if not contact_sheets:
                    missing.append("contact-sheet")
                raise ValueError(
                    "world-buyer 最终产物不完整，缺少：" + ", ".join(missing)
                )

            kept = [latest_by_slot[slot] for slot in range(1, 6)]
            kept.append(contact_sheets[-1])
            return self._remove_rejected_images(
                image_outputs,
                kept,
                "已清理 {count} 张 world-buyer 候选图，最终保留 5 张产品卡和 1 张总览图。",
            )

        if skill_name == "batch-clothing-white-bg-images" and image_paths:
            expected = len(image_paths)
            kept = image_outputs[-expected:]
            return self._remove_rejected_images(
                image_outputs,
                kept,
                "已移除 {count} 张重试候选图，按一张输入一张输出保留最终版。",
            )

        if skill_name != "batch-clothing-product-images":
            return image_outputs

        expected = self._requested_product_image_count(prompt)
        if len(image_outputs) <= expected:
            return image_outputs

        # 复核重做仍使用 001/002/003 等槽位编号；后生成的同槽图片替换旧候选。
        latest_by_slot = {}
        for item in image_outputs:
            slot = self._numbered_output_slot(item)
            if slot is not None and 1 <= slot <= expected:
                latest_by_slot[slot] = item
        if all(slot in latest_by_slot for slot in range(1, expected + 1)):
            kept = [latest_by_slot[slot] for slot in range(1, expected + 1)]
        else:
            kept = image_outputs[-expected:]

        return self._remove_rejected_images(
            image_outputs,
            kept,
            f"已替换 {{count}} 张复核淘汰图，批量服装主图最终保留 {expected} 张。",
        )

    async def route(self, prompt, skill_override, image_paths, input_path=""):
        self._record("status", "正在分析任务、素材和 Skill 路由…")
        decision = route_with_rules(
            self.registry,
            prompt,
            skill_override=skill_override,
            image_count=len(image_paths),
            input_path=input_path,
        )
        if decision.skill_name:
            self._record(
                "route",
                f"已选择 Skill：{decision.skill_name}",
                **decision.to_dict(),
            )
            return decision

        catalog = json.dumps(self.registry.catalog(), ensure_ascii=False)
        instructions = (
            "Select exactly one skill for the user's task. Do not execute it. "
            "Use only a name from the provided catalog. Infer image roles and missing hard inputs. "
            "Use confidence below 0.75 when the task cannot be routed safely.\n\n"
            f"Skill catalog: {catalog}"
        )
        router = Agent(
            name="ComfyUI Skill Router",
            instructions=instructions,
            model=self.model,
            model_settings=self._settings(max_tokens=2048),
            output_type=RouterOutput,
        )
        result = await Runner.run(
            router,
            self._input_items(prompt, image_paths),
            max_turns=2,
            hooks=self.hooks,
            run_config=RunConfig(
                tracing_disabled=True,
                workflow_name="ComfyUI skill routing",
                reasoning_item_id_policy="omit",
            ),
        )
        output = result.final_output
        self.registry.get(output.skill_name)
        decision = RouteDecision(
            skill_name=output.skill_name,
            mode=output.mode,
            confidence=output.confidence,
            input_roles=output.input_roles,
            missing_inputs=output.missing_inputs,
            reason=output.reason,
        )
        self._record(
            "route",
            f"已选择 Skill：{decision.skill_name}",
            **decision.to_dict(),
        )
        return decision

    def _tools(self, skill, input_paths):
        runtime = self

        async def list_input_files() -> str:
            """List the validated input image files available to this task."""
            runtime._record("tool_start", "正在检查输入文件…", tool="list_input_files")
            runtime._record(
                "tool_end",
                f"输入文件检查完成，共 {len(input_paths)} 个",
                tool="list_input_files",
                count=len(input_paths),
            )
            return json.dumps([str(path) for path in input_paths], ensure_ascii=False)

        async def read_skill_resource(relative_path: str) -> str:
            """Read a reference file belonging to the selected skill."""
            runtime._record(
                "tool_start",
                f"正在读取 Skill 参考资料：{relative_path}",
                tool="read_skill_resource",
            )
            text = skill.read_resource(relative_path)
            runtime._record(
                "tool_end",
                f"参考资料读取完成：{relative_path}",
                tool="read_skill_resource",
                path=relative_path,
            )
            return text[:50000]

        async def generate_image(prompt: str, n: int, size: str, output_name: str) -> str:
            """Generate images with the configured Vapeur image model and save final PNG files."""
            runtime._record(
                "image_prompt",
                f"图片提示词：\n{prompt}",
                tool="generate_image",
            )
            runtime._record(
                "tool_start",
                f"正在调用 {runtime.image_model} 生成图片…",
                tool="generate_image",
                count=n,
                size=size,
            )
            images = await runtime.image_client.generate(
                prompt=prompt,
                model=runtime.image_model,
                n=n,
                size=size,
            )
            records = save_generated_images(images, runtime.artifact_store, output_name)
            runtime._record(
                "tool_end",
                f"图片生成完成，共 {len(records)} 张",
                tool="generate_image",
                count=len(records),
                paths=[item.path for item in records],
            )
            return json.dumps([item.disk_dict() for item in records], ensure_ascii=False)

        async def edit_images(
            prompt: str,
            image_indices: list[int],
            n: int,
            size: str,
            output_name: str,
        ) -> str:
            """Edit selected input images. Pass an empty image_indices list to use all inputs."""
            selected = input_paths
            if image_indices:
                selected = []
                for index in image_indices:
                    if index < 1 or index > len(input_paths):
                        raise ValueError(f"image index {index} is out of range.")
                    selected.append(input_paths[index - 1])
            runtime._record(
                "image_prompt",
                f"图片编辑提示词：\n{prompt}",
                tool="edit_images",
            )
            runtime._record(
                "tool_start",
                f"正在调用 {runtime.image_model} 编辑 {len(selected)} 张参考图…",
                tool="edit_images",
                input_count=len(selected),
                output_count=n,
                size=size,
            )
            images = await runtime.image_client.edit(
                prompt=prompt,
                image_paths=selected,
                model=runtime.image_model,
                n=n,
                size=size,
                mask=runtime.mask_path,
            )
            records = save_generated_images(images, runtime.artifact_store, output_name)
            runtime._record(
                "tool_end",
                f"图片编辑完成，共 {len(records)} 张",
                tool="edit_images",
                count=len(records),
                paths=[item.path for item in records],
            )
            return json.dumps([item.disk_dict() for item in records], ensure_ascii=False)

        async def inspect_generated_image(image_name: str, checklist: str) -> str:
            """Inspect one generated image by its exact filename returned by an image tool."""
            output = runtime._output_by_name(runtime.artifact_store.records, image_name)
            filename = Path(output.path).name
            runtime._record(
                "tool_start",
                f"正在复核生成图片：{filename}",
                tool="inspect_generated_image",
                image_name=filename,
            )
            response = await runtime.client.responses.create(
                model=runtime.agent_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": checklist},
                            {
                                "type": "input_image",
                                "image_url": image_data_url(output.path),
                                "detail": "high",
                            },
                        ],
                    }
                ],
                max_output_tokens=2048,
                store=False,
            )
            inspection_result = str(response.output_text or "").strip()
            runtime._record(
                "inspection_result",
                f"图片复核结果（{filename}）：\n{inspection_result}",
                tool="inspect_generated_image",
                image_name=filename,
            )
            runtime._record(
                "tool_end",
                f"生成图片复核完成：{filename}",
                tool="inspect_generated_image",
                image_name=filename,
            )
            return inspection_result

        async def make_contact_sheet(image_indices: list[int], output_name: str) -> str:
            """Compose existing generated images into a deterministic contact sheet."""
            outputs = [item for item in runtime.artifact_store.records if item.kind == "output"]
            selected = outputs if not image_indices else []
            for index in image_indices:
                if index < 1 or index > len(outputs):
                    raise ValueError(f"image index {index} is out of range.")
                selected.append(outputs[index - 1])
            runtime._record(
                "tool_start",
                f"正在合成 {len(selected)} 张图片的总览板…",
                tool="make_contact_sheet",
                count=len(selected),
            )
            record = compose_contact_sheet(
                [item.path for item in selected], runtime.artifact_store, output_name=output_name
            )
            runtime._record(
                "tool_end",
                "总览板合成完成",
                tool="make_contact_sheet",
                path=record.path,
            )
            return json.dumps(record.disk_dict(), ensure_ascii=False)

        async def run_skill_script(script_name: str, arguments: list[str]) -> str:
            """Run one Python script from the selected skill's scripts directory without a shell."""
            scripts_dir = (skill.path / "scripts").resolve()
            script = (scripts_dir / Path(script_name).name).resolve()
            if scripts_dir not in script.parents or not script.is_file() or script.suffix.lower() != ".py":
                raise ValueError(f"Skill script is not allowed: {script_name}")
            for argument in arguments:
                candidate = Path(argument).expanduser()
                if candidate.is_absolute() and not _is_within(candidate.resolve(), runtime.allowed_paths):
                    raise ValueError(f"Script path argument is outside allowed roots: {argument}")
            runtime._record(
                "tool_start",
                f"正在运行 Skill 脚本：{script.name}",
                tool="run_skill_script",
                script=script.name,
            )
            process = await asyncio.create_subprocess_exec(
                runtime.script_python,
                str(script),
                *[str(item) for item in arguments],
                cwd=str(skill.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise ValueError("Skill script exceeded the 300 second timeout.")
            result = {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace")[:10000],
                "stderr": stderr.decode("utf-8", errors="replace")[:10000],
            }
            runtime._record(
                "tool_end",
                f"Skill 脚本执行完成：{script.name}",
                tool="run_skill_script",
                script=script.name,
                returncode=process.returncode,
            )
            return json.dumps(result, ensure_ascii=False)

        return [
            function_tool(list_input_files),
            function_tool(read_skill_resource),
            function_tool(generate_image),
            function_tool(edit_images),
            function_tool(inspect_generated_image),
            function_tool(make_contact_sheet),
            function_tool(run_skill_script),
        ]

    async def execute(self, prompt, decision, image_paths):
        skill = self.registry.get(decision.skill_name)
        text_only = wants_text_only(prompt)
        required_image_tool = None if text_only else (
            "edit_images" if image_paths else "generate_image"
        )
        self._record("status", f"正在执行 Skill：{skill.name}…")
        contract = f"""

<runtime_contract>
You are executing the selected skill inside one ComfyUI node.
Selected mode: {decision.mode}
Delivery mode: {"text only" if text_only else "image artifacts required"}
Use the provided function tools to produce the actual deliverables; never claim an image or file exists unless a tool returned it.
Original input files are numbered in the order returned by list_input_files.
Use edit_images when visual references must be preserved and generate_image when there is no visual reference.
When image artifacts are required, a final text response before an image tool has successfully returned is invalid.
Inspect important generated images against the skill quality gate. Retry only when a concrete defect is found.
Call inspect_generated_image with the exact output filename returned by generate_image or edit_images. Never infer an image from list position, numeric index, or tool completion order.
For a retry, keep the original leading numeric slot and add `_重做` or `_final` to output_name so the old candidate is replaced.
Use run_skill_script only for scripts explicitly shipped under this skill's scripts directory.
Finish with a concise Chinese summary. Do not expose credentials or signed URL query parameters.
</runtime_contract>
"""
        agent = Agent(
            name=f"Skill: {skill.name}",
            instructions=skill.instructions + contract,
            model=self.model,
            model_settings=self._settings(tool_choice=required_image_tool),
            tools=self._tools(skill, image_paths),
        )
        task = (
            f"用户请求：{prompt}\n"
            f"已选择 skill：{decision.skill_name}\n"
            f"执行模式：{decision.mode}\n"
            f"本地输出目录：{self.artifact_store.outputs_dir}\n"
            f"可用输入文件：{json.dumps([str(path) for path in image_paths], ensure_ascii=False)}"
        )
        result = await Runner.run(
            agent,
            self._input_items(task, image_paths),
            max_turns=self.max_turns,
            hooks=self.hooks,
            run_config=RunConfig(
                tracing_disabled=True,
                workflow_name=f"ComfyUI skill {skill.name}",
                reasoning_item_id_policy="omit",
            ),
        )
        image_outputs = [
            item
            for item in self.artifact_store.records
            if item.kind == "output" and item.content_type.startswith("image/")
        ]
        if not text_only and not image_outputs:
            raise ValueError(
                f"Skill {skill.name} 未生成任何图片产物，任务已终止，不会返回黑色占位图。"
            )
        image_outputs = self._enforce_output_contract(
            skill.name, image_paths, image_outputs, prompt=prompt
        )
        self._record("completed", f"Skill 执行完成：{skill.name}", skill=skill.name)
        return str(result.final_output)

    async def close(self):
        await self.client.close()
