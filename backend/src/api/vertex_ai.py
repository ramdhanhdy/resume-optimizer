"""Vertex AI client for non-Google models (e.g., Claude Sonnet 4.5) with streaming and cost tracking.

This client is intentionally separate from gemini.py to keep Gemini API and
Vertex AI concerns isolated. It currently focuses on Anthropic models via
Vertex AI using the AnthropicVertex SDK.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Generator, Optional

from anthropic import AnthropicVertex

from .pricing import CostBreakdown, TokenUsage, get_pricing_manager


class VertexClient:
    """Client for interacting with Vertex AI-hosted LLMs (Anthropic, etc.)."""

    def __init__(self) -> None:
        """Initialize Vertex client.

        Auth uses Application Default Credentials (ADC). On Cloud Run, ensure
        the service account has Vertex AI + Anthropic permissions.

        Env variables:
            VERTEX_PROJECT_ID: GCP project id
            VERTEX_LOCATION: default region (e.g., us-east5 for Sonnet 4.5)
        """
        project_id = os.getenv("VERTEX_PROJECT_ID")
        location = os.getenv("VERTEX_LOCATION", "us-east5")

        if not project_id:
            raise ValueError("VERTEX_PROJECT_ID is required for VertexClient")

        self.client = AnthropicVertex(project_id=project_id, region=location)

        self.last_request_cost = 0.0
        self.total_cost = 0.0
        self.last_usage: Optional[TokenUsage] = None
        self.last_cost_breakdown: Optional[CostBreakdown] = None
        self.pricing_manager = get_pricing_manager()

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
        thinking_budget: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        stop: Optional[Any] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from a Vertex-hosted model.

        Args mirror other provider clients; unsupported params are ignored.

        For AnthropicVertex, we map to messages.create/stream with a single
        user message containing the combined system + user text.
        """
        # Anthropic messages: system prompt should ideally be a separate
        # system-level message. For now, we combine for simplicity.
        user_content_parts = []
        if prompt:
            user_content_parts.append(prompt)
        if text_content:
            user_content_parts.append(text_content)
        if file_path and file_type:
            # For now we only note the presence of a file, since file
            # attachments to AnthropicVertex require a more complex flow.
            user_content_parts.append(
                f"[Attachment: {os.path.basename(file_path)} ({file_type})]"
            )

        combined_content = "\n\n".join(user_content_parts) or "No content provided"

        # Build request kwargs, filtering unsupported fields
        request_kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": combined_content,
                }
            ],
        }

        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if stop is not None:
            request_kwargs["stop_sequences"] = stop if isinstance(stop, list) else [stop]
        # AnthropicVertex currently ignores frequency/presence_penalty, top_k,
        # seed, and thinking_budget; we leave them out intentionally.

        full_response = ""

        try:
            # Stream text output using AnthropicVertex streaming API
            with self.client.messages.stream(**request_kwargs) as stream:
                for text in stream.text_stream:
                    if text:
                        full_response += text
                        yield text
        except Exception as exc:
            raise Exception(f"Vertex AI (Anthropic) error: {str(exc)}") from exc

        # Cost tracking. The current AnthropicVertex streaming docs don't expose
        # explicit token counts on the stream, so we fall back to estimation
        # similar to other clients when usage metadata is unavailable.
        input_tokens = self.pricing_manager.estimate_tokens(
            prompt + (text_content or "")
        )
        output_tokens = self.pricing_manager.estimate_tokens(full_response)

        token_usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
        cost_breakdown = self.pricing_manager.calculate_cost("vertex", model, token_usage)

        self.last_usage = token_usage
        self.last_cost_breakdown = cost_breakdown
        self.last_request_cost = cost_breakdown.total_cost
        self.total_cost += cost_breakdown.total_cost

        return {
            "full_response": full_response,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": token_usage.total_tokens,
            "cost": cost_breakdown.total_cost,
            "cost_breakdown": {
                "input_cost": cost_breakdown.input_cost,
                "output_cost": cost_breakdown.output_cost,
                "platform_fee": cost_breakdown.platform_fee,
                "total_cost": cost_breakdown.total_cost,
            },
            "model": model,
        }

    def get_last_usage(self) -> Optional[TokenUsage]:
        return self.last_usage

    def get_last_cost(self) -> float:
        return self.last_request_cost

    def get_total_cost(self) -> float:
        return self.total_cost

    def reset_total_cost(self) -> None:
        self.total_cost = 0.0


__all__ = ["VertexClient"]
