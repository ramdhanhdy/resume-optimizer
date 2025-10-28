"""Multi-provider facade that routes requests to the correct client per model.

This class exposes a superset of provider parameters but filters and forwards
only what the underlying provider supports, providing a stable interface for
agents/services.
"""

from __future__ import annotations

from typing import Any, Dict, Generator, Optional

from .client_factory import get_client
from .model_registry import get_capabilities, get_api_model, supports_thinking_budget
from .types import CompletionRequest, GenerationConfig


class MultiProviderClient:
    """Facade over provider-specific clients (OpenRouter, LongCat, ...)."""

    def __init__(self) -> None:
        # No heavy init; provider clients are created lazily via the factory
        self.last_request_cost = 0.0
        self.total_cost = 0.0

    def stream_completion(
        self,
        *,
        prompt: str,
        model: str,
        text_content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 5000,
        thinking_budget: Optional[int] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        caps = get_capabilities(model)
        api_model = get_api_model(model)
        client = get_client(model)

        # Build call and filter per provider/capabilities
        kwargs: Dict[str, Any] = {
            "prompt": prompt,
            "model": api_model,
            "text_content": text_content,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if caps.get("supports_files"):
            if file_path:
                kwargs["file_path"] = file_path
            if file_type:
                kwargs["file_type"] = file_type

        if thinking_budget is not None and supports_thinking_budget(model):
            kwargs["thinking_budget"] = thinking_budget

        # Dispatch and stream
        stream = client.stream_completion(**kwargs)

        full_response = ""
        try:
            while True:
                chunk = next(stream)
                if isinstance(chunk, str):
                    full_response += chunk
                yield chunk
        except StopIteration as exc:
            meta = exc.value if exc.value else {}
            # Try to pull cost metadata off the underlying client if present
            try:
                self.last_request_cost = getattr(client, "last_request_cost", 0.0)
                # Some clients track cumulative cost
                self.total_cost += self.last_request_cost
            except Exception:
                pass
            return meta

    def get_last_cost(self) -> float:
        return self.last_request_cost

    def get_total_cost(self) -> float:
        return self.total_cost

    def reset_total_cost(self) -> None:
        self.total_cost = 0.0

    # Optional provider-agnostic DTO entrypoint
    def stream(
        self,
        request: CompletionRequest,
        *,
        model: str,
        provider_options: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        gen: GenerationConfig = request.get("generation", {})  # type: ignore[assignment]
        return self.stream_completion(
            prompt=request.get("system_prompt", ""),
            model=model,
            text_content=request.get("user_text"),
            file_path=request.get("file_path"),
            file_type=request.get("file_type"),
            temperature=float(gen.get("temperature", 0.7)) if gen else 0.7,
            max_tokens=int(gen.get("max_tokens", 4000)) if gen else 4000,
            thinking_budget=(provider_options or {}).get("thinking_budget"),
        )


__all__ = ["MultiProviderClient"]
