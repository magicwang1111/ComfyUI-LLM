import asyncio
import base64
import io
import json
import os
from pathlib import Path
from urllib.parse import quote

import httpx
import numpy as np
from PIL import Image

from .models import (
    DEFAULT_THINKING_LEVEL,
    THINKING_LEVELS,
    VAPEUR_BASE_URL,
    model_spec,
)

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "config.local.json"
DEFAULT_TIMEOUT = 600
DEFAULT_RETRIES = 1
DEFAULT_RETRY_DELAY = 2.0

_CLAUDE_MANUAL_BUDGETS = {
    "low": 1024,
    "medium": 8192,
    "high": 32768,
}


class VapeurAPIError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Vapeur API error {status_code}: {message}")


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {CONFIG_PATH.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{CONFIG_PATH.name} must contain a JSON object.")
    return data


def _positive_int(value, name, default):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if parsed < 0 if name == "request_retries" else parsed <= 0:
        raise ValueError(f"{name} must be {'non-negative' if name == 'request_retries' else 'positive'}.")
    return parsed


def resolve_runtime_config():
    data = load_config()
    api_key = str(data.get("VAPEUR_API_KEY") or "").strip()
    if not api_key:
        api_key = os.getenv("VAPEUR_API_KEY", "").strip()
    if not api_key and str(data.get("api_provider") or "").strip().lower() == "vapeur":
        api_key = str(data.get("api_key") or "").strip()
    if not api_key:
        raise ValueError(
            "VAPEUR_API_KEY is required in config.local.json or the environment."
        )

    timeout = _positive_int(data.get("request_timeout"), "request_timeout", DEFAULT_TIMEOUT)
    retries = _positive_int(data.get("request_retries"), "request_retries", DEFAULT_RETRIES)
    try:
        retry_delay = float(data.get("retry_delay", DEFAULT_RETRY_DELAY))
    except (TypeError, ValueError) as exc:
        raise ValueError("retry_delay must be a non-negative number.") from exc
    if retry_delay < 0:
        raise ValueError("retry_delay must be a non-negative number.")

    return {
        "api_key": api_key,
        "timeout": timeout,
        "max_retries": retries,
        "retry_delay": retry_delay,
    }


def validate_common(provider, model, thinking_level, system_prompt, user_prompt, image=None):
    spec = model_spec(provider, model)
    if thinking_level not in THINKING_LEVELS:
        raise ValueError(f"thinking_level must be one of: {', '.join(THINKING_LEVELS)}.")
    if not isinstance(system_prompt, str):
        raise ValueError("system_prompt must be a string.")
    if not isinstance(user_prompt, str) or not user_prompt.strip():
        raise ValueError("user_prompt is required.")
    if image is not None and not spec["vision"]:
        raise ValueError(f"{model} does not support image input in this node.")
    return spec


def encode_single_image(image):
    if hasattr(image, "detach"):
        array = image.detach().cpu().numpy()
    else:
        array = np.asarray(image)

    if array.ndim != 4:
        raise ValueError("IMAGE input must be a ComfyUI image batch in BHWC format.")
    if array.shape[0] != 1:
        raise ValueError("Exactly one image is supported; provide an IMAGE batch of size 1.")

    array = array[0]
    if array.ndim != 3 or array.shape[-1] not in (3, 4):
        raise ValueError("IMAGE input must have 3 RGB or 4 RGBA channels.")

    pixels = np.clip(array, 0.0, 1.0)
    pixels = np.rint(pixels * 255.0).astype(np.uint8)
    pil_image = Image.fromarray(pixels, mode="RGBA" if pixels.shape[-1] == 4 else "RGB")
    output = io.BytesIO()
    pil_image.save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode("ascii")


def _openai_messages(system_prompt, user_prompt, image_b64=None):
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    if image_b64:
        content = [
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
            },
        ]
    else:
        content = user_prompt
    messages.append({"role": "user", "content": content})
    return messages


def build_gpt_payload(model, thinking_level, system_prompt, user_prompt, image_b64=None):
    spec = validate_common("gpt", model, thinking_level, system_prompt, user_prompt)
    return {
        "model": model,
        "messages": _openai_messages(system_prompt, user_prompt, image_b64),
        "max_completion_tokens": spec["max_tokens"],
        "reasoning_effort": "none" if thinking_level == "off" else thinking_level,
        "stream": False,
    }


def build_deepseek_payload(model, thinking_level, system_prompt, user_prompt):
    spec = validate_common("deepseek", model, thinking_level, system_prompt, user_prompt)
    payload = {
        "model": model,
        "messages": _openai_messages(system_prompt, user_prompt),
        "max_tokens": spec["max_tokens"],
        "thinking": {"type": "disabled" if thinking_level == "off" else "enabled"},
        "stream": False,
    }
    if thinking_level != "off":
        payload["reasoning_effort"] = thinking_level
    return payload


def build_claude_payload(model, thinking_level, system_prompt, user_prompt, image_b64=None):
    spec = validate_common("claude", model, thinking_level, system_prompt, user_prompt)
    content = []
    if image_b64:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64,
                },
            }
        )
    if system_prompt.strip():
        prompt_text = (
            f"<system_instructions>\n{system_prompt.strip()}\n</system_instructions>\n\n"
            f"<user_request>\n{user_prompt}\n</user_request>"
        )
    else:
        prompt_text = user_prompt
    content.append({"type": "text", "text": prompt_text})

    payload = {
        "model": model,
        "max_tokens": spec["max_tokens"],
        "messages": [{"role": "user", "content": content}],
        "stream": False,
    }

    mode = spec["thinking_mode"]
    if mode == "always_adaptive":
        payload["output_config"] = {
            "effort": "low" if thinking_level == "off" else thinking_level
        }
    elif mode == "adaptive_default":
        if thinking_level == "off":
            payload["thinking"] = {"type": "disabled"}
        else:
            payload["output_config"] = {"effort": thinking_level}
    elif mode == "adaptive_optional" and thinking_level != "off":
        payload["thinking"] = {"type": "adaptive"}
        payload["output_config"] = {"effort": thinking_level}
    elif mode == "manual" and thinking_level != "off":
        payload["thinking"] = {
            "type": "enabled",
            "budget_tokens": _CLAUDE_MANUAL_BUDGETS[thinking_level],
        }
    return payload


def build_gemini_payload(model, thinking_level, system_prompt, user_prompt, image_b64=None):
    spec = validate_common("gemini", model, thinking_level, system_prompt, user_prompt)
    parts = [{"text": user_prompt}]
    if image_b64:
        parts.append(
            {
                "inlineData": {
                    "mimeType": "image/png",
                    "data": image_b64,
                }
            }
        )

    if thinking_level == "off":
        mapped_level = "minimal" if spec["supports_minimal"] else "low"
    else:
        mapped_level = thinking_level

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "maxOutputTokens": spec["max_tokens"],
            "thinkingConfig": {"thinkingLevel": mapped_level},
        },
    }
    if system_prompt.strip():
        payload["systemInstruction"] = {"parts": [{"text": system_prompt.strip()}]}
    return payload


def build_request(provider, model, thinking_level, system_prompt, user_prompt, image=None):
    image_b64 = encode_single_image(image) if image is not None else None
    if provider == "gpt":
        return "/v1/chat/completions", build_gpt_payload(
            model, thinking_level, system_prompt, user_prompt, image_b64
        )
    if provider == "deepseek":
        if image is not None:
            raise ValueError("DeepSeek node does not support image input.")
        return "/v1/chat/completions", build_deepseek_payload(
            model, thinking_level, system_prompt, user_prompt
        )
    if provider == "claude":
        return "/claude/v1/messages", build_claude_payload(
            model, thinking_level, system_prompt, user_prompt, image_b64
        )
    if provider == "gemini":
        path = f"/gemini/v1beta/models/{quote(model, safe='')}:generateContent"
        return path, build_gemini_payload(
            model, thinking_level, system_prompt, user_prompt, image_b64
        )
    raise ValueError(f"Unsupported provider: {provider}")


def extract_text(provider, response):
    try:
        if provider in {"gpt", "deepseek"}:
            content = response["choices"][0]["message"]["content"]
            if isinstance(content, str):
                text = content
            else:
                text = "".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and part.get("type") in {"text", "output_text"}
                )
        elif provider == "claude":
            text = "".join(
                part.get("text", "")
                for part in response["content"]
                if isinstance(part, dict) and part.get("type") == "text"
            )
        elif provider == "gemini":
            text = "".join(
                part.get("text", "")
                for part in response["candidates"][0]["content"]["parts"]
                if isinstance(part, dict) and not part.get("thought", False)
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected {provider} response structure.") from exc

    if not text.strip():
        raise ValueError(f"{provider} response did not contain final text.")
    return text


def response_json(response):
    return json.dumps(response, ensure_ascii=False, indent=2)


def _error_message(response):
    try:
        payload = response.json()
        error = payload.get("error", payload)
        if isinstance(error, dict):
            return str(error.get("message") or error.get("type") or error)[:1000]
        return str(error)[:1000]
    except (ValueError, AttributeError):
        return response.text[:1000] or response.reason_phrase


class VapeurLLMClient:
    def __init__(
        self,
        api_key,
        timeout=DEFAULT_TIMEOUT,
        max_retries=DEFAULT_RETRIES,
        retry_delay=DEFAULT_RETRY_DELAY,
        transport=None,
    ):
        self.api_key = api_key
        self.max_retries = max(0, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self._client = httpx.AsyncClient(
            base_url=VAPEUR_BASE_URL,
            timeout=httpx.Timeout(float(timeout)),
            transport=transport,
        )

    def _headers(self, provider):
        if provider in {"gpt", "deepseek"}:
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8",
            }
        if provider == "claude":
            return {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json; charset=utf-8",
            }
        if provider == "gemini":
            return {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json; charset=utf-8",
            }
        raise ValueError(f"Unsupported provider: {provider}")

    async def generate(self, provider, path, payload):
        attempts = self.max_retries + 1
        request_body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        for attempt in range(attempts):
            try:
                response = await self._client.post(
                    path,
                    headers=self._headers(provider),
                    content=request_body,
                )
                if response.status_code >= 400:
                    raise VapeurAPIError(response.status_code, _error_message(response))
                return response.json()
            except VapeurAPIError:
                raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt + 1 >= attempts:
                    raise ValueError(
                        f"Vapeur {provider} request failed after {attempts} attempt(s): "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
                if self.retry_delay:
                    await asyncio.sleep(self.retry_delay)
        raise RuntimeError("unreachable")

    async def close(self):
        await self._client.aclose()


def create_runtime_client():
    return VapeurLLMClient(**resolve_runtime_config())
