"""OpenAI API client with streaming support and cost tracking.

This client talks directly to api.openai.com using the official
`openai` SDK, and mirrors the interface used by other provider
clients so it can be used transparently via the MultiProviderClient.
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Generator, List, Literal, Optional, Sequence, TypedDict, Union

from openai import OpenAI

from .pricing import CostBreakdown, TokenUsage, get_pricing_manager


class _TextContentParam(TypedDict):
    type: Literal["text"]
    text: str


class _ImageUrlParam(TypedDict):
    url: str


class _ImageContentParam(TypedDict):
    type: Literal["image_url"]
    image_url: _ImageUrlParam


ContentPartParam = Union[_TextContentParam, _ImageContentParam]


class _SystemMessageParam(TypedDict):
    role: Literal["system"]
    content: str


class _UserMessageParam(TypedDict):
    role: Literal["user"]
    content: Sequence[ContentPartParam]


ChatMessageParam = Union[_SystemMessageParam, _UserMessageParam]


class OpenAIClient:
    """Client for interacting with the OpenAI API directly."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, reads from env `OPENAI_API_KEY`.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Default base_url points to api.openai.com
        self.client: Any = OpenAI(api_key=self.api_key)

        self.last_request_cost = 0.0
        self.total_cost = 0.0
        self.last_usage: Optional[TokenUsage] = None
        self.last_cost_breakdown: Optional[CostBreakdown] = None
        self.pricing_manager = get_pricing_manager()

    def _encode_file(self, file_path: str) -> str:
        """Encode file to base64 for API transmission."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _prepare_content(
        self,
        text: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> List[ContentPartParam]:
        """Prepare content for API request.

        Mirrors the structure used by other OpenAI-compatible clients
        (OpenRouter, Zenmux, Cerebras) so MultiProviderClient can
        treat them uniformly.
        """
        content: List[ContentPartParam] = []

        if text:
            content.append({"type": "text", "text": text})

        if file_path and file_type:
            # For images, send as data URL similar to other providers
            if file_type.startswith("image/"):
                encoded = self._encode_file(file_path)
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{file_type};base64,{encoded}",
                        },
                    }
                )
            else:
                # For documents, send a textual note
                content.append(
                    {
                        "type": "text",
                        "text": (
                            f"[Document attached: {os.path.basename(file_path)}]"\
                            "\nPlease analyze the content of this document."
                        ),
                    }
                )

        if content:
            return content

        return [{"type": "text", "text": "No content provided"}]

    def stream_completion(
        self,
        *,
        prompt: str,
        model: str,
        text_content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        thinking_budget: Optional[int] = None,  # Unsupported but accepted for parity
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,  # Ignored by OpenAI Chat API
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from OpenAI API.

        Args mirror other provider clients so MultiProviderClient can
        pass a unified set of arguments. Unsupported params are
        safely ignored.
        """
        content = self._prepare_content(text_content, file_path, file_type)

        messages: List[ChatMessageParam] = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ]

        try:
            # Build base parameters shared across models
            params: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }

            # Newer reasoning-style models (e.g., gpt-5.1, o1) expect
            # `max_completion_tokens` instead of `max_tokens`.
            model_lower = model.lower()
            uses_completion_tokens = (
                model_lower.startswith("gpt-5")
                or model_lower.startswith("o1")
                or model_lower.startswith("o3")
            )

            if max_tokens is not None:
                if uses_completion_tokens:
                    params["max_completion_tokens"] = max_tokens
                else:
                    params["max_tokens"] = max_tokens

            if top_p is not None:
                params["top_p"] = top_p
            if frequency_penalty is not None:
                params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                params["presence_penalty"] = presence_penalty
            if seed is not None:
                params["seed"] = seed
            if stop is not None:
                params["stop"] = stop

            # `thinking_budget` and `top_k` are not standard OpenAI chat
            # parameters; we intentionally omit them here.

            stream: Any = self.client.chat.completions.create(**params)

            full_response = ""
            usage_data: Any = None

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_response += delta
                    yield delta

                # Capture usage data if present on the final chunk
                if hasattr(chunk, "usage") and chunk.usage:
                    usage_data = chunk.usage

            # Extract token usage if available, otherwise fall back to estimation
            if usage_data is not None:
                input_tokens = getattr(usage_data, "prompt_tokens", 0)
                output_tokens = getattr(usage_data, "completion_tokens", 0)
                total_tokens = getattr(
                    usage_data,
                    "total_tokens",
                    input_tokens + output_tokens,
                )
            else:
                input_tokens = self.pricing_manager.estimate_tokens(prompt + (text_content or ""))
                output_tokens = self.pricing_manager.estimate_tokens(full_response)
                total_tokens = input_tokens + output_tokens

            usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )
            cost_breakdown = self.pricing_manager.calculate_cost("openai", model, usage)

            self.last_usage = usage
            self.last_cost_breakdown = cost_breakdown
            self.last_request_cost = cost_breakdown.total_cost
            self.total_cost += cost_breakdown.total_cost

            return {
                "full_response": full_response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost_breakdown.total_cost,
                "cost_breakdown": {
                    "input_cost": cost_breakdown.input_cost,
                    "output_cost": cost_breakdown.output_cost,
                    "platform_fee": cost_breakdown.platform_fee,
                    "total_cost": cost_breakdown.total_cost,
                },
                "model": model,
            }

        except Exception as exc:  # pragma: no cover - network / API errors
            raise Exception(f"OpenAI API error: {exc}") from exc

    def get_last_usage(self) -> Optional[TokenUsage]:
        return self.last_usage

    def get_last_cost_breakdown(self) -> Optional[CostBreakdown]:
        return self.last_cost_breakdown

    def get_last_cost(self) -> float:
        return self.last_request_cost

    def get_total_cost(self) -> float:
        return self.total_cost

    def reset_total_cost(self) -> None:
        self.total_cost = 0.0


__all__ = ["OpenAIClient"]
