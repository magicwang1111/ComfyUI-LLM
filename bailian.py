"""Direct Alibaba Cloud Model Studio (百炼) Qwen calls through the OpenAI-compatible API.

Independent of Vapeur: uses BAILIAN_API_KEY and the workspace base URL.
Requests are always streamed (Qwen3.5-Omni rejects non-streaming calls) and
aggregated into a chat.completion-shaped dict.
"""
import asyncio
import base64
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path

import httpx

from .llm import (
    DEFAULT_RETRIES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_TIMEOUT,
    RETRYABLE_HTTP_STATUS_CODES,
    _error_message,
    _positive_int,
    encode_single_image,
    load_config,
)
from .models import THINKING_LEVELS, VIDEO_SYSTEM_PROMPT  # noqa: F401 (re-export)

logger = logging.getLogger(__name__)

DEFAULT_BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com"
CHAT_PATH = "/compatible-mode/v1/chat/completions"
UPLOAD_PATH = "/api/v1/uploads"
# Bailian rejects Base64 video strings of 10 MB or more; larger clips go through
# the free temporary storage (oss://, 48 h, bound to the model and account).
MAX_BASE64_VIDEO_CHARS = 9_500_000
MAX_VIDEO_BYTES = 1024 * 1024 * 1024

# audio: understands the video's sound track. thinking: how thinking_level maps.
#   effort      -> reasoning_effort (none/low/medium/xhigh)
#   effort_min  -> same, but "off" maps to "low" (audio is ignored without thinking)
#   budget      -> enable_thinking + thinking_budget
#   none        -> no thinking parameters
BAILIAN_MODELS = {
    "qwen3.8-omni-flash": {"audio": True, "thinking": "effort_min"},
    "qwen3.5-omni-plus": {"audio": True, "thinking": "none"},
    "qwen3.5-omni-flash": {"audio": True, "thinking": "none"},
    "qwen3.8-max": {"audio": False, "thinking": "effort"},
    "qwen3.8-flash": {"audio": False, "thinking": "effort"},
    "qwen3.7-max": {"audio": False, "thinking": "budget"},
    "qwen3.7-plus": {"audio": False, "thinking": "budget"},
    "qwen3.7-flash": {"audio": False, "thinking": "budget"},
    "qwen3.6-plus": {"audio": False, "thinking": "budget"},
    "qwen3.6-flash": {"audio": False, "thinking": "budget"},
}
DEFAULT_BAILIAN_MODEL = "qwen3.8-omni-flash"
_EFFORTS = {"off": "none", "low": "low", "medium": "medium", "high": "xhigh"}
_BUDGETS = {"low": 4096, "medium": 16384}



class BailianAPIError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"百炼 API error {status_code}: {message}")


def resolve_bailian_config():
    data = load_config()
    api_key = str(data.get("BAILIAN_API_KEY") or "").strip()
    if not api_key:
        api_key = (os.getenv("BAILIAN_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "BAILIAN_API_KEY is required in config.local.json "
            "(or the BAILIAN_API_KEY / DASHSCOPE_API_KEY environment variable)."
        )
    base_url = str(
        data.get("BAILIAN_BASE_URL") or os.getenv("BAILIAN_BASE_URL") or DEFAULT_BAILIAN_BASE_URL
    ).strip().rstrip("/")
    for suffix in ("/compatible-mode/v1", "/api/v1"):
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    try:
        retry_delay = float(data.get("retry_delay", DEFAULT_RETRY_DELAY))
    except (TypeError, ValueError) as exc:
        raise ValueError("retry_delay must be a non-negative number.") from exc
    return {
        "api_key": api_key,
        "base_url": base_url,
        "timeout": _positive_int(data.get("request_timeout"), "request_timeout", DEFAULT_TIMEOUT),
        "max_retries": _positive_int(data.get("request_retries"), "request_retries", DEFAULT_RETRIES),
        "retry_delay": max(0.0, retry_delay),
    }


def thinking_params(model, thinking_level):
    if thinking_level not in THINKING_LEVELS:
        raise ValueError(f"thinking_level must be one of: {', '.join(THINKING_LEVELS)}.")
    mode = BAILIAN_MODELS[model]["thinking"]
    if mode == "effort_min":
        return {"reasoning_effort": _EFFORTS["low" if thinking_level == "off" else thinking_level]}
    if mode == "effort":
        return {"reasoning_effort": _EFFORTS[thinking_level]}
    if mode == "budget":
        if thinking_level == "off":
            return {"enable_thinking": False}
        params = {"enable_thinking": True}
        if thinking_level in _BUDGETS:
            params["thinking_budget"] = _BUDGETS[thinking_level]
        return params
    return {}


def build_bailian_payload(model, thinking_level, system_prompt, user_prompt, image_b64=None, video_url=None):
    if model not in BAILIAN_MODELS:
        raise ValueError(f"Unsupported 百炼 model: {model}")
    if not isinstance(user_prompt, str) or not user_prompt.strip():
        raise ValueError("user_prompt is required.")
    messages = []
    if isinstance(system_prompt, str) and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    if image_b64 or video_url:
        content = []
        if video_url:
            content.append({"type": "video_url", "video_url": {"url": video_url}})
        if image_b64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}})
        content.append({"type": "text", "text": user_prompt})
    else:
        content = user_prompt
    messages.append({"role": "user", "content": content})
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if model.startswith("qwen3.5-omni"):
        payload["modalities"] = ["text"]
    payload.update(thinking_params(model, thinking_level))
    return payload


def save_video_mp4(video, directory):
    # save_to keeps the VIDEO object's audio and active trim window.
    path = Path(directory) / "input.mp4"
    video.save_to(str(path), format="mp4", codec="h264")
    size = path.stat().st_size
    if not size:
        raise ValueError("VIDEO input is empty.")
    if size > MAX_VIDEO_BYTES:
        raise ValueError("VIDEO input exceeds the 1 GB 百炼 upload limit. Trim or compress it first.")
    return path


def aggregate_stream(lines):
    """Merge chat.completion.chunk SSE lines into one chat.completion dict."""
    content, reasoning = [], []
    result = {"object": "chat.completion"}
    finish_reason = None
    for line in lines:
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        chunk = json.loads(data)
        if "error" in chunk:
            error = chunk["error"]
            message = error.get("message", error) if isinstance(error, dict) else error
            raise BailianAPIError(chunk.get("status_code", 500), str(message)[:1000])
        for key in ("id", "model", "created"):
            if chunk.get(key) is not None:
                result[key] = chunk[key]
        if chunk.get("usage"):
            result["usage"] = chunk["usage"]
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            content.append(delta.get("content") or "")
            reasoning.append(delta.get("reasoning_content") or "")
            finish_reason = choice.get("finish_reason") or finish_reason
    message = {"role": "assistant", "content": "".join(content)}
    if any(reasoning):
        message["reasoning_content"] = "".join(reasoning)
    result["choices"] = [{"index": 0, "message": message, "finish_reason": finish_reason}]
    return result


def _uses_temp_url(payload):
    for message in payload.get("messages", []):
        content = message.get("content")
        if isinstance(content, list):
            for item in content:
                url = (item.get("video_url") or item.get("image_url") or {}).get("url", "")
                if url.startswith("oss://"):
                    return True
    return False


class BailianClient:
    def __init__(self, api_key, base_url=DEFAULT_BAILIAN_BASE_URL, timeout=DEFAULT_TIMEOUT,
                 max_retries=DEFAULT_RETRIES, retry_delay=DEFAULT_RETRY_DELAY, transport=None):
        self.api_key = api_key
        self.max_retries = max(0, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self._client = httpx.AsyncClient(
            base_url=base_url, timeout=httpx.Timeout(float(timeout)), transport=transport,
        )

    async def upload_temp_file(self, model, path):
        """Upload to Bailian's free temporary storage and return an oss:// URL."""
        response = await self._client.get(
            UPLOAD_PATH,
            params={"action": "getPolicy", "model": model},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if response.status_code >= 400:
            raise BailianAPIError(response.status_code, f"getPolicy failed: {_error_message(response)}")
        policy = response.json()["data"]
        key = f"{policy['upload_dir']}/{uuid.uuid4().hex}.mp4"
        with open(path, "rb") as handle:
            upload = await self._client.post(
                policy["upload_host"],
                data={
                    "OSSAccessKeyId": policy["oss_access_key_id"],
                    "Signature": policy["signature"],
                    "policy": policy["policy"],
                    "x-oss-object-acl": policy["x_oss_object_acl"],
                    "x-oss-forbid-overwrite": policy["x_oss_forbid_overwrite"],
                    "key": key,
                    "success_action_status": "200",
                },
                files={"file": ("input.mp4", handle, "video/mp4")},
            )
        if upload.status_code != 200:
            raise BailianAPIError(upload.status_code, f"temporary upload failed: {upload.text[:500]}")
        return f"oss://{key}"

    async def chat(self, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }
        if _uses_temp_url(payload):
            headers["X-DashScope-OssResourceResolve"] = "enable"
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                async with self._client.stream("POST", CHAT_PATH, headers=headers, content=body) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        raise BailianAPIError(response.status_code, _error_message(response))
                    lines = [line async for line in response.aiter_lines()]
                return aggregate_stream(lines)
            except BailianAPIError as exc:
                if exc.status_code not in RETRYABLE_HTTP_STATUS_CODES or attempt + 1 >= attempts:
                    raise
                logger.warning("百炼 HTTP %s; retry %s/%s", exc.status_code, attempt + 1, self.max_retries)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt + 1 >= attempts:
                    raise ValueError(
                        f"百炼 request failed after {attempts} attempt(s): {type(exc).__name__}: {exc}"
                    ) from exc
            if self.retry_delay:
                await asyncio.sleep(self.retry_delay)
        raise RuntimeError("unreachable")

    async def close(self):
        await self._client.aclose()


def create_bailian_client():
    return BailianClient(**resolve_bailian_config())


async def video_reference(client, model, video):
    """Return a Base64 data URL for small clips, else a temporary oss:// URL."""
    with tempfile.TemporaryDirectory(prefix="comfyui-llm-bailian-") as directory:
        path = await asyncio.to_thread(save_video_mp4, video, directory)
        if (path.stat().st_size + 2) // 3 * 4 <= MAX_BASE64_VIDEO_CHARS:
            data = await asyncio.to_thread(path.read_bytes)
            return "data:;base64," + base64.b64encode(data).decode("ascii")
        return await client.upload_temp_file(model, path)


def extract_bailian_text(response):
    try:
        choice = response["choices"][0]
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected 百炼 response structure.") from exc
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"百炼 response did not contain final text (finish_reason={choice.get('finish_reason')}).")
    return text


async def generate_bailian(model, thinking_level, system_prompt, user_prompt, image=None, video=None):
    image_b64 = encode_single_image(image) if image is not None else None
    client = create_bailian_client()
    try:
        video_url = await video_reference(client, model, video) if video is not None else None
        payload = build_bailian_payload(model, thinking_level, system_prompt, user_prompt, image_b64, video_url)
        return await client.chat(payload)
    finally:
        await client.close()
