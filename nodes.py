from .llm import (
    VapeurAPIError,
    build_request,
    create_runtime_client,
    extract_text,
    response_json,
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


NODE_CLASS_MAPPINGS = {
    f"{NODE_PREFIX} GPT": GPTLLMNode,
    f"{NODE_PREFIX} Claude": ClaudeLLMNode,
    f"{NODE_PREFIX} Gemini": GeminiLLMNode,
    f"{NODE_PREFIX} DeepSeek": DeepSeekLLMNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {name: name for name in NODE_CLASS_MAPPINGS}

