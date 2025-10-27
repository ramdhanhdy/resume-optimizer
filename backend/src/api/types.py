"""Common types for provider-agnostic LLM requests."""

from __future__ import annotations

from typing import Optional, TypedDict


class GenerationConfig(TypedDict, total=False):
    temperature: float
    max_tokens: int


class CompletionRequest(TypedDict, total=False):
    """Provider-agnostic request payload for chat completion."""

    system_prompt: str
    user_text: Optional[str]
    file_path: Optional[str]
    file_type: Optional[str]
    generation: GenerationConfig


__all__ = ["GenerationConfig", "CompletionRequest"]

