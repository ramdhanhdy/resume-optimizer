"""Gemini API client with streaming support and cost tracking."""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Generator, Optional

from google import genai
from google.genai import types


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
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from Gemini API.

        Args:
            prompt: System instruction/prompt
            model: Model identifier (e.g., 'gemini-2.5-flash')
            text_content: Text input from user
            file_path: Path to uploaded file
            file_type: MIME type of file
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_budget: Thinking budget for models that support it

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

            # Calculate cost based on actual token usage
            input_tokens = 0
            output_tokens = 0

            if usage_metadata:
                input_tokens = getattr(usage_metadata, "prompt_token_count", 0)
                output_tokens = getattr(usage_metadata, "candidates_token_count", 0)
            else:
                # Fallback to estimation if metadata not available
                input_tokens = self._estimate_tokens(prompt + (text_content or ""))
                output_tokens = self._estimate_tokens(full_response)

            cost = self._calculate_cost(model, input_tokens, output_tokens)
            self.last_request_cost = cost
            self.total_cost += cost

            return {
                "full_response": full_response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "model": model,
            }

        except Exception as exc:
            raise Exception(f"Gemini API error: {str(exc)}") from exc

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4 if text else 0

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on Gemini pricing.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (includes thinking tokens)

        Returns:
            Cost in USD
        """
        # Pricing per million tokens (as of Oct 2025)
        # Free tier exists but we'll use paid tier pricing for cost tracking
        pricing = {
            "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
            "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
            "gemini-2.5-flash-preview-09-2025": {"input": 0.30, "output": 2.50},
            "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
            "gemini-2.5-flash-lite-preview-09-2025": {"input": 0.10, "output": 0.40},
            "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
            "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
        }

        # Default pricing if model not found
        default_price = {"input": 0.30, "output": 2.50}
        model_price = pricing.get(model, default_price)

        input_cost = (input_tokens / 1_000_000) * model_price["input"]
        output_cost = (output_tokens / 1_000_000) * model_price["output"]

        return input_cost + output_cost

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
