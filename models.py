NODE_PREFIX = "ComfyUI-LLM"
NODE_CATEGORY = NODE_PREFIX

VAPEUR_BASE_URL = "https://api.vapeur.ai"
THINKING_LEVELS = ["off", "low", "medium", "high"]
DEFAULT_THINKING_LEVEL = "medium"

DEFAULT_SYSTEM_PROMPT = """你是中文短视频口播稿编辑。保留原稿中的事实、数字、专有名词和核心观点，不虚构信息。用有吸引力的开场钩子，删除重复、空话和书面表达，改写为自然、简短、有停顿感的口语句子；必要时按“钩子—核心信息—结论或行动”重排结构，默认不超过原稿长度。若提供图片，只使用可以明确确认的视觉信息，不作无依据推断。只输出优化后的完整口播稿，不解释、不加标题、不使用 Markdown。"""

MODEL_SPECS = {
    "gpt": {
        "default": "gpt-5.5",
        "models": {
            # Vapeur GPT text catalog, checked 2026-11-04; GPT-6.1 Sol output limit from OpenAI docs.
            "gpt-6.1-terra": {"max_tokens": 128000, "vision": True},
            "gpt-6.1-sol": {"max_tokens": 128000, "vision": True, "min_thinking": "low"},
            "gpt-6-astra": {"max_tokens": 128000, "vision": True, "min_thinking": "low"},
            "gpt-6-sol": {"max_tokens": 128000, "vision": True},
            "gpt-6-luna": {"max_tokens": 128000, "vision": True},
            "gpt-5.6-sol": {"max_tokens": 128000, "vision": True},
            "gpt-5.6-terra": {"max_tokens": 128000, "vision": True},
            "gpt-5.6-luna": {"max_tokens": 128000, "vision": True},
            "gpt-chat-latest": {"max_tokens": 128000, "vision": False, "reasoning": False},
            "gpt-5.5": {"max_tokens": 128000, "vision": True},
            "gpt-5.4": {"max_tokens": 128000, "vision": True},
            "gpt-5.4-pro": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "medium"},
            "gpt-5.4-mini": {"max_tokens": 128000, "vision": True},
            "gpt-5.4-nano": {"max_tokens": 128000, "vision": True},
            "gpt-5.3-codex": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "low"},
            "gpt-5.2": {"max_tokens": 128000, "vision": True},
            "gpt-5.2-codex": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "low"},
            "gpt-5.1": {"max_tokens": 128000, "vision": True},
            "gpt-5.1-codex": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "low"},
            "gpt-5.1-codex-mini": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "low"},
            "gpt-5.1-codex-max": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "low"},
            "gpt-5": {"max_tokens": 128000, "vision": True, "off_effort": "minimal"},
            "gpt-5-mini": {"max_tokens": 128000, "vision": True, "off_effort": "minimal"},
            "gpt-5-nano": {"max_tokens": 128000, "vision": True, "off_effort": "minimal"},
            "gpt-5-pro": {"max_tokens": 272000, "vision": True, "api": "responses", "min_thinking": "high"},
            "gpt-5-codex": {"max_tokens": 128000, "vision": True, "api": "responses", "min_thinking": "low"},
            "gpt-4.1": {"max_tokens": 32768, "vision": True, "reasoning": False},
            "gpt-4.1-mini": {"max_tokens": 32768, "vision": True, "reasoning": False},
            "gpt-4.1-nano": {"max_tokens": 32768, "vision": True, "reasoning": False},
            "gpt-4o": {"max_tokens": 16384, "vision": True, "reasoning": False},
        },
    },
    "claude": {
        "default": "claude-sonnet-5",
        "models": {
            "claude-fable-5": {
                "max_tokens": 128000,
                "vision": True,
                "thinking_mode": "always_adaptive",
            },
            "claude-opus-4-8": {
                "max_tokens": 128000,
                "vision": True,
                "thinking_mode": "adaptive_optional",
            },
            "claude-sonnet-5": {
                "max_tokens": 128000,
                "vision": True,
                "thinking_mode": "adaptive_default",
            },
            "claude-haiku-4-5": {
                "max_tokens": 64000,
                "vision": True,
                "thinking_mode": "manual",
            },
        },
    },
    "gemini": {
        "default": "gemini-3.5-flash",
        "models": {
            # Vapeur model hub / Google thinking levels, checked 2026-09-22.
            "gemini-3.8-flash": {"max_tokens": 65536, "vision": True, "supports_minimal": False},
            "gemini-3.7-flash": {"max_tokens": 65536, "vision": True, "supports_minimal": False},
            "gemini-3.6-flash": {"max_tokens": 65536, "vision": True, "supports_minimal": True},
            "gemini-3.5-flash": {"max_tokens": 65536, "vision": True, "supports_minimal": True},
            "gemini-3.5-flash-lite": {
                "max_tokens": 65536,
                "vision": True,
                "supports_minimal": True,
            },
            "gemini-3.1-pro-preview": {
                "max_tokens": 65536,
                "vision": True,
                "supports_minimal": False,
            },
            "gemini-3.1-flash-lite": {
                "max_tokens": 65536,
                "vision": True,
                "supports_minimal": True,
            },
            "gemini-3-flash-preview": {
                "max_tokens": 65536,
                "vision": True,
                "supports_minimal": True,
            },
            "gemini-2.5-flash": {
                "max_tokens": 65536,
                "vision": True,
                "thinking_budgets": {"off": 0, "low": 1024, "medium": 8192, "high": 24576},
            },
        },
    },
    "deepseek": {
        "default": "deepseek-v4-flash-cn",
        "models": {
            "deepseek-v4-pro-cn": {"max_tokens": 131072, "vision": False},
            "deepseek-v4-flash-cn": {"max_tokens": 131072, "vision": False},
        },
    },
    "qwen": {
        "default": "qwen3.7-max",
        "models": {
            # All Qwen chat models in Vapeur's model hub, checked 2026-11-03.
            "qwen3.8-max": {"vision": True},
            "qwen3.8-flash": {"vision": True},
            "qwen3.8-max-glb": {"vision": True},
            "qwen3.7-max": {"vision": True},
            "qwen3.7-plus": {"vision": True},
            "qwen3.7-flash": {"vision": True},
            "qwen3.7-max-glb": {"vision": True},
            "qwen3.6-plus": {"vision": True},
            "qwen3.6-flash": {"vision": True},
            "qwen3.6-plus-glb": {"vision": True},
            "qwen3.6-flash-glb": {"vision": True},
            "qwen3.5-plus": {"vision": True},
            "qwen3.5-flash": {"vision": True},
            "qwen3.5-plus-glb": {"vision": True},
            "qwen3.5-flash-glb": {"vision": True},
            "qwen-plus-latest": {"vision": False},
        },
    },
}

# Vapeur model-square prices, checked 2026-11-04. USD per 1M tokens.
GPT_PRICING = {
    "gpt-6.1-terra": {
        "standard": {"input": 1, "cached_input": 0.05, "output": 5},
        "long_context": {"input": 2, "cached_input": 0.1, "output": 7.5},
        "long_context_threshold": 272000,
    },
    "gpt-6.1-sol": {
        "standard": {"input": 2, "cached_input": 0.1, "output": 10},
        "long_context": {"input": 4, "cached_input": 0.2, "output": 15},
        "long_context_threshold": 272000,
    },
    "gpt-6-astra": {
        "standard": {"input": 10, "cached_input": 1, "output": 50},
        "long_context": {"input": 20, "cached_input": 2, "output": 75},
        "long_context_threshold": 272000,
    },
    "gpt-6-sol": {
        "standard": {"input": 2, "cached_input": 0.2, "output": 10},
        "long_context": {"input": 4, "cached_input": 0.4, "output": 15},
        "long_context_threshold": 272000,
    },
    "gpt-6-luna": {
        "standard": {"input": 0.1, "cached_input": 0.01, "output": 0.5},
        "long_context": {"input": 0.2, "cached_input": 0.02, "output": 0.75},
        "long_context_threshold": 272000,
    },
    "gpt-5.6-sol": {
        "standard": {"input": 4, "cached_input": 0.4, "output": 20},
        "long_context": {"input": 8, "cached_input": 0.8, "output": 30},
        "long_context_threshold": 272000,
    },
    "gpt-5.6-terra": {
        "standard": {"input": 2, "cached_input": 0.2, "output": 12},
        "long_context": {"input": 4, "cached_input": 0.4, "output": 18},
        "long_context_threshold": 272000,
    },
    "gpt-5.6-luna": {
        "standard": {"input": 0.2, "cached_input": 0.02, "output": 1.2},
        "long_context": {"input": 0.4, "cached_input": 0.04, "output": 1.8},
        "long_context_threshold": 272000,
    },
    "gpt-chat-latest": {
        "standard": {"input": 5, "cached_input": 0.5, "output": 30},
    },
    "gpt-5.5": {
        "standard": {"input": 5, "cached_input": 0.5, "output": 30},
        "long_context": {"input": 10, "cached_input": 1, "output": 45},
        "long_context_threshold": 272000,
    },
    "gpt-5.4": {
        "standard": {"input": 2.5, "cached_input": 0.25, "output": 15},
        "long_context": {"input": 5, "cached_input": 0.5, "output": 22.5},
        "long_context_threshold": 272000,
    },
    "gpt-5.4-pro": {
        "standard": {"input": 30, "cached_input": 30, "output": 180},
        "long_context": {"input": 60, "cached_input": 60, "output": 270},
        "long_context_threshold": 272000,
    },
    "gpt-5.4-mini": {
        "standard": {"input": 0.75, "cached_input": 0.08, "output": 4.5},
    },
    "gpt-5.4-nano": {
        "standard": {"input": 0.2, "cached_input": 0.02, "output": 1.25},
    },
    "gpt-5.3-codex": {
        "standard": {"input": 1.75, "cached_input": 0.18, "output": 14},
    },
    "gpt-5.2": {
        "standard": {"input": 1.75, "cached_input": 0.18, "output": 14},
    },
    "gpt-5.2-codex": {
        "standard": {"input": 1.75, "cached_input": 0.18, "output": 14},
    },
    "gpt-5.1": {
        "standard": {"input": 1.25, "cached_input": 0.13, "output": 10},
    },
    "gpt-5.1-codex": {
        "standard": {"input": 1.25, "cached_input": 0.13, "output": 10},
    },
    "gpt-5.1-codex-mini": {
        "standard": {"input": 0.25, "cached_input": 0.03, "output": 2},
    },
    "gpt-5.1-codex-max": {
        "standard": {"input": 1.25, "cached_input": 0.13, "output": 10},
    },
    "gpt-5": {
        "standard": {"input": 1.25, "cached_input": 0.13, "output": 10},
    },
    "gpt-5-mini": {
        "standard": {"input": 0.25, "cached_input": 0.03, "output": 2},
    },
    "gpt-5-nano": {
        "standard": {"input": 0.05, "cached_input": 0.01, "output": 0.4},
    },
    "gpt-5-pro": {
        "standard": {"input": 15, "cached_input": 15, "output": 120},
    },
    "gpt-5-codex": {
        "standard": {"input": 1.25, "cached_input": 0.13, "output": 10},
    },
    "gpt-4.1": {
        "standard": {"input": 2, "cached_input": 0.5, "output": 8},
    },
    "gpt-4.1-mini": {
        "standard": {"input": 0.4, "cached_input": 0.1, "output": 1.6},
    },
    "gpt-4.1-nano": {
        "standard": {"input": 0.1, "cached_input": 0.03, "output": 0.4},
    },
    "gpt-4o": {
        "standard": {"input": 2.5, "cached_input": 1.25, "output": 10},
    },
}


def model_names(provider):
    return list(MODEL_SPECS[provider]["models"])


def default_model(provider):
    return MODEL_SPECS[provider]["default"]


def model_spec(provider, model):
    try:
        return MODEL_SPECS[provider]["models"][model]
    except KeyError as exc:
        raise ValueError(f"Unsupported {provider} model: {model}") from exc


def gpt_pricing(model):
    try:
        return GPT_PRICING[model]
    except KeyError as exc:
        raise ValueError(f"Pricing is unavailable for GPT model: {model}") from exc
