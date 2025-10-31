"""Factory helpers for selecting the appropriate LLM client per model."""

from __future__ import annotations

from typing import Dict, Optional, Union, cast

from .cerebras import CerebrasClient
from .gemini import GeminiClient
from .longcat import LongCatClient
from .model_registry import get_provider_for_model
from .openrouter import OpenRouterClient
from .zenmux import ZenmuxClient

ClientType = Union[OpenRouterClient, LongCatClient, ZenmuxClient, GeminiClient, CerebrasClient]

_CLIENT_CACHE: Dict[str, ClientType] = {}


def _get_cached(provider: str, factory) -> ClientType:
    if provider not in _CLIENT_CACHE:
        _CLIENT_CACHE[provider] = factory()
    return _CLIENT_CACHE[provider]


def get_client(
    model: str,
    *,
    default_client: Optional[ClientType] = None,
) -> ClientType:
    """Return the appropriate API client for the requested model."""

    provider = get_provider_for_model(model)

    if provider == "longcat":
        return cast(ClientType, _get_cached("longcat", LongCatClient))

    if provider == "zenmux":
        return cast(ClientType, _get_cached("zenmux", ZenmuxClient))

    if provider == "gemini":
        return cast(ClientType, _get_cached("gemini", GeminiClient))

    if provider == "cerebras":
        return cast(ClientType, _get_cached("cerebras", CerebrasClient))

    # Default to OpenRouter (including unknown providers that fall back)
    if default_client is not None and isinstance(default_client, OpenRouterClient):
        return default_client

    return cast(ClientType, _get_cached("openrouter", OpenRouterClient))


def create_client():
    """Create a multi-provider client facade with lazy provider init.

    This keeps server code simple while allowing agents to route per-model
    to the correct underlying provider client.
    """
    # Imported lazily to avoid circular import at module load time
    from .multiprovider import MultiProviderClient

    return MultiProviderClient()
