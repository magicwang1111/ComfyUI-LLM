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
            "gpt-5.6-sol": {"max_tokens": 128000, "vision": True},
            "gpt-5.6-terra": {"max_tokens": 128000, "vision": True},
            "gpt-5.6-luna": {"max_tokens": 128000, "vision": True},
            "gpt-5.5": {"max_tokens": 128000, "vision": True},
            "gpt-5.4": {"max_tokens": 128000, "vision": True},
            "gpt-5.4-mini": {"max_tokens": 128000, "vision": True},
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
            "gemini-3.5-flash": {"max_tokens": 65536, "vision": True, "supports_minimal": True},
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
        },
    },
    "deepseek": {
        "default": "deepseek-v4-flash-cn",
        "models": {
            "deepseek-v4-pro-cn": {"max_tokens": 131072, "vision": False},
            "deepseek-v4-flash-cn": {"max_tokens": 131072, "vision": False},
        },
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
