"""Model → provider registry and capability helpers.

Provides lightweight mapping and conservative fallbacks so new models work
without explicit entries while enabling provider-specific capability checks.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, TypedDict

ProviderName = Literal["openrouter", "longcat", "zenmux", "gemini", "cerebras"]


class Capabilities(TypedDict, total=False):
    supports_files: bool
    supports_images: bool
    supports_thinking_budget: bool


class ModelInfo(TypedDict, total=False):
    provider: ProviderName
    capabilities: Capabilities
    api_model: str


def _norm(model: str) -> str:
    return (model or "").strip().lower()


MODEL_REGISTRY: Dict[str, ModelInfo] = {
    # LongCat / Meituan
    "longcat-flash-chat": {
        "provider": "longcat",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "LongCat-Flash-Chat",
    },
    "meituan::longcat-flash-chat": {
        "provider": "longcat",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "LongCat-Flash-Chat",
    },
    "longcat-flash-thinking": {
        "provider": "longcat",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": True,
        },
        "api_model": "LongCat-Flash-Thinking",
    },
    "meituan::longcat-flash-thinking": {
        "provider": "longcat",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": True,
        },
        "api_model": "LongCat-Flash-Thinking",
    },
    # OpenRouter
    "qwen/qwen3-max": {
        "provider": "openrouter",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
        },
        "api_model": "qwen/qwen3-max",
    },
    "openrouter::qwen/qwen3-max": {
        "provider": "openrouter",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
        },
        "api_model": "qwen/qwen3-max",
    },
    "openai/gpt-5.1": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "openai/gpt-5.1",
    },
    "openrouter::openai/gpt-5.1": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "openai/gpt-5.1",
    },
    "openrouter::moonshotai/kimi-k2-thinking": {
        "provider": "openrouter",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": True,
        },
        "api_model": "moonshotai/kimi-k2-thinking",
    },
    "google/gemini-2.0-flash-exp:free": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "google/gemini-2.0-flash-exp:free",
    },
    "openrouter::google/gemini-2.0-flash-exp:free": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "google/gemini-2.0-flash-exp:free",
    },
    "anthropic/claude-sonnet-4.5": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "anthropic/claude-sonnet-4.5",
    },
    "openrouter::anthropic/claude-sonnet-4.5": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "anthropic/claude-sonnet-4.5",
    },
    "openai/gpt-5": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "openai/gpt-5",
    },
    "openrouter::openai/gpt-5": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "openai/gpt-5",
    },
    "x-ai/grok-4-fast": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "x-ai/grok-4-fast",
    },
    "openrouter::x-ai/grok-4-fast": {
        "provider": "openrouter",
        "capabilities": {"supports_files": True, "supports_images": True},
        "api_model": "x-ai/grok-4-fast",
    },
    # Zenmux aliases (already prefixed)
    "zenmux::openai/gpt-5": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "openai/gpt-5",
    },
    "zenmux::anthropic/claude-sonnet-4.5": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "anthropic/claude-sonnet-4.5",
    },
    "zenmux::anthropic/claude-haiku-4.5": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "anthropic/claude-haiku-4.5",
    },
    "zenmux::google/gemini-2.5-pro": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": False,
        },
        "api_model": "google/gemini-2.5-pro",
    },
    "zenmux::google/gemini-2.5-flash": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": False,
        },
        "api_model": "google/gemini-2.5-flash",
    },
    "zenmux::google/gemini-2.5-flash-lite": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": True,  # Requires value between 512-24576
        },
        "api_model": "google/gemini-2.5-flash-lite",
    },
    "zenmux::moonshotai/kimi-k2-0905": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": False,
        },
        "api_model": "moonshotai/kimi-k2-0905"
    },
    "zenmux::inclusionai/ring-mini-2.0": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "inclusionai/ring-mini-2.0"
    },
    "zenmux::inclusionai/ring-flash-2.0": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": False,
        },
        "api_model": "inclusionai/ring-flash-2.0"
    },
    "zenmux::minimax/minimax-m2": {
        "provider": "zenmux",
        "capabilities": {
            "supports_files": True,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "minimax/minimax-m2"
    },
    # Cerebras models
    "cerebras::qwen-3-235b-a22b-instruct-2507": {
        "provider": "cerebras",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "qwen-3-235b-a22b-instruct-2507",
    },
    "cerebras::gpt-oss-120b": {
        "provider": "cerebras",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "gpt-oss-120b",
    },
    "cerebras::qwen-3-coder-480b": {
        "provider": "cerebras",
        "capabilities": {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        },
        "api_model": "qwen-3-coder-480b",
    },
    # Gemini models
    "gemini::gemini-2.5-flash": {
        "provider": "gemini",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": True,
        },
        "api_model": "gemini-2.5-flash",
    },
    "gemini::gemini-2.5-pro": {
        "provider": "gemini",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": True,
        },
        "api_model": "gemini-2.5-pro",
    },
    "gemini::gemini-2.5-flash-lite": {
        "provider": "gemini",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": True,
        },
        "api_model": "gemini-2.5-flash-lite",
    },
    "gemini::gemini-2.0-flash": {
        "provider": "gemini",
        "capabilities": {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": False,
        },
        "api_model": "gemini-2.0-flash",
    },
}


def get_provider_for_model(model: str) -> ProviderName:
    m = _norm(model)
    info = MODEL_REGISTRY.get(m)
    if info and "provider" in info:
        return info["provider"]  # type: ignore[return-value]

    # Conservative fallback: infer by prefix
    if m.startswith("longcat"):
        return "longcat"
    if m.startswith("meituan::"):
        return "longcat"
    if m.startswith("openrouter::"):
        return "openrouter"
    if m.startswith("zenmux::"):
        return "zenmux"
    if m.startswith("gemini::"):
        return "gemini"
    if m.startswith("cerebras::"):
        return "cerebras"
    return "openrouter"


def get_capabilities(model: str) -> Capabilities:
    m = _norm(model)
    info = MODEL_REGISTRY.get(m)
    if info and "capabilities" in info:
        return info["capabilities"]

    provider = get_provider_for_model(model)
    # Defaults per provider
    if provider == "longcat":
        return {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": (m == "longcat-flash-thinking"),
        }
    if provider == "zenmux":
        return {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        }
    if provider == "gemini":
        return {
            "supports_files": True,
            "supports_images": True,
            "supports_thinking_budget": ("2.5" in m),  # Only 2.5 models support thinking
        }
    if provider == "cerebras":
        return {
            "supports_files": False,
            "supports_images": False,
            "supports_thinking_budget": False,
        }
    # openrouter default
    return {
        "supports_files": True,
        "supports_images": True,
        "supports_thinking_budget": False,
    }


def supports_thinking_budget(model: str) -> bool:
    caps = get_capabilities(model)
    return bool(caps.get("supports_thinking_budget"))


def get_api_model(model: str) -> str:
    m = _norm(model)
    info = MODEL_REGISTRY.get(m)
    if info and "api_model" in info:
        return info["api_model"]

    if m.startswith("zenmux::"):
        return model.split("::", 1)[1]
    if m.startswith("openrouter::"):
        return model.split("::", 1)[1]
    if m.startswith("meituan::"):
        return model.split("::", 1)[1]
    if m.startswith("gemini::"):
        return model.split("::", 1)[1]
    if m.startswith("cerebras::"):
        return model.split("::", 1)[1]
    return model


__all__ = [
    "ProviderName",
    "Capabilities",
    "ModelInfo",
    "MODEL_REGISTRY",
    "get_provider_for_model",
    "get_capabilities",
    "supports_thinking_budget",
    "get_api_model",
]

