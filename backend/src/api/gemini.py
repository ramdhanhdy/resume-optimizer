"""Gemini API client with streaming support and cost tracking."""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Generator, Optional

from google import genai
from google.genai import types

from .pricing import get_pricing_manager, TokenUsage, CostBreakdown


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key. If not provided, reads from env.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided")

        self.client = genai.Client(api_key=self.api_key)

        self.last_request_cost = 0.0
        self.total_cost = 0.0
        self.last_usage: Optional[TokenUsage] = None
        self.last_cost_breakdown: Optional[CostBreakdown] = None
        self.pricing_manager = get_pricing_manager()

    def _encode_file(self, file_path: str) -> str:
        """Encode file to base64 for API transmission.

        Args:
            file_path: Path to file

        Returns:
            Base64 encoded file content
        """
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _prepare_content_parts(
        self,
        text: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        """Prepare content parts for API request.

        Args:
            text: Text content
            file_path: Path to uploaded file
            file_type: MIME type of file

        Returns:
            List of content parts for Gemini API
        """
        parts = []

        if text:
            parts.append({"text": text})

        if file_path and file_type:
            # For images, use inline_data
            if file_type.startswith("image/"):
                encoded = self._encode_file(file_path)
                parts.append({
                    "inline_data": {
                        "mime_type": file_type,
                        "data": encoded,
                    }
                })
            # For PDFs and documents, note them in text
            else:
                parts.append({
                    "text": (
                        f"[Document attached: {os.path.basename(file_path)}]\n"
                        "Please analyze the content of this document."
                    )
                })

        if not parts:
            parts.append({"text": "No content provided"})

        return parts

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
        stop: Optional[List[str]] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from Gemini API.

        Args:
            prompt: System instruction/prompt
            model: Model identifier (e.g., 'gemini-2.5-flash')
            text_content: Text input from user
            file_path: Path to uploaded file
            file_type: MIME type of file
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            thinking_budget: Thinking budget for models that support it
            top_p: Nucleus sampling threshold (0.0-1.0)
            top_k: Top-k sampling limit
            frequency_penalty: Penalize token frequency (0.0-1.0 for Gemini)
            presence_penalty: Penalize token presence (0.0-1.0 for Gemini)
            seed: Random seed for deterministic outputs
            stop: Stop sequences (list of strings)

        Yields:
            Response chunks as they arrive

        Returns:
            Final metadata including cost information
        """
        # Prepare content parts
        content_parts = self._prepare_content_parts(text_content, file_path, file_type)

        # Build config
        config_kwargs: Dict[str, Any] = {
            "system_instruction": prompt,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Add optional parameters (Gemini uses camelCase for some)
        if top_p is not None:
            config_kwargs["top_p"] = top_p
        if top_k is not None:
            config_kwargs["top_k"] = top_k
        if frequency_penalty is not None:
            # Gemini uses 0.0-1.0 range, normalize if needed
            config_kwargs["frequency_penalty"] = max(0.0, min(1.0, frequency_penalty))
        if presence_penalty is not None:
            # Gemini uses 0.0-1.0 range, normalize if needed
            config_kwargs["presence_penalty"] = max(0.0, min(1.0, presence_penalty))
        if seed is not None:
            config_kwargs["seed"] = seed
        if stop is not None:
            config_kwargs["stop_sequences"] = stop if isinstance(stop, list) else [stop]

        # Add thinking config if budget is specified and model supports it
        if thinking_budget is not None and "2.5" in model:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=thinking_budget
            )

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            # Stream the response
            response_stream = self.client.models.generate_content_stream(
                model=model,
                contents=[{"parts": content_parts}],
                config=config,
            )

            full_response = ""
            usage_metadata = None

            for chunk in response_stream:
                # Extract text from chunk
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text

                # Capture usage metadata from last chunk
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage_metadata = chunk.usage_metadata

            # Extract token usage from metadata
            input_tokens = 0
            output_tokens = 0
            thinking_tokens = 0

            if usage_metadata:
                input_tokens = getattr(usage_metadata, "prompt_token_count", 0)
                # candidates_token_count includes both output and thinking tokens
                total_candidate_tokens = getattr(usage_metadata, "candidates_token_count", 0)
                # Extract thinking tokens if available (Gemini 2.5 models)
                thinking_tokens = getattr(usage_metadata, "thoughts_token_count", 0)
                output_tokens = total_candidate_tokens - thinking_tokens
            else:
                # Fallback to estimation if metadata not available
                input_tokens = self.pricing_manager.estimate_tokens(prompt + (text_content or ""))
                output_tokens = self.pricing_manager.estimate_tokens(full_response)

            # Calculate cost using pricing manager
            usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                thinking_tokens=thinking_tokens,
                total_tokens=input_tokens + output_tokens + thinking_tokens
            )
            cost_breakdown = self.pricing_manager.calculate_cost("gemini", model, usage)
            
            self.last_usage = usage
            self.last_cost_breakdown = cost_breakdown
            self.last_request_cost = cost_breakdown.total_cost
            self.total_cost += cost_breakdown.total_cost

            return {
                "full_response": full_response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "thinking_tokens": thinking_tokens,
                "total_tokens": usage.total_tokens,
                "cost": cost_breakdown.total_cost,
                "cost_breakdown": {
                    "input_cost": cost_breakdown.input_cost,
                    "output_cost": cost_breakdown.output_cost,
                    "thinking_cost": cost_breakdown.thinking_cost,
                    "total_cost": cost_breakdown.total_cost,
                },
                "model": model,
            }

        except Exception as exc:
            raise Exception(f"Gemini API error: {str(exc)}") from exc

    def get_last_usage(self) -> Optional[TokenUsage]:
        """Get token usage from last request."""
        return self.last_usage
    
    def get_last_cost_breakdown(self) -> Optional[CostBreakdown]:
        """Get detailed cost breakdown from last request."""
        return self.last_cost_breakdown

    def get_last_cost(self) -> float:
        """Get cost of last request."""
        return self.last_request_cost

    def get_total_cost(self) -> float:
        """Get cumulative cost across requests."""
        return self.total_cost

    def reset_total_cost(self) -> None:
        """Reset total cost counter."""
        self.total_cost = 0.0


__all__ = ["GeminiClient"]
