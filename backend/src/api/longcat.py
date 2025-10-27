"""LongCat API client with streaming support and cost tracking."""

from __future__ import annotations

import os
from typing import Any, Dict, Generator, Optional

from openai import OpenAI


class LongCatClient:
    """Client for interacting with Meituan LongCat API."""

    _BASE_URL = "https://api.longcat.chat/openai"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize LongCat client.

        Args:
            api_key: LongCat API key. If not provided, reads from env.
        """
        self.api_key = api_key or os.getenv("LONGCAT_API_KEY")
        if not self.api_key:
            raise ValueError("LongCat API key not provided")

        self.client: Any = OpenAI(base_url=self._BASE_URL, api_key=self.api_key)

        self.last_request_cost = 0.0
        self.total_cost = 0.0

    def stream_completion(
        self,
        *,
        prompt: str,
        model: str = "LongCat-Flash-Chat",
        text_content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 10000,
        thinking_budget: Optional[int] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from LongCat API.

        Args:
            prompt: System prompt
            model: Model identifier (LongCat-Flash-Chat / LongCat-Flash-Thinking)
            text_content: Text input from user
            file_path: Unsupported for LongCat (included for signature parity)
            file_type: Unsupported for LongCat (included for signature parity)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_budget: Thinking time budget in tokens (LongCat-Flash-Thinking only)

        Yields:
            Response chunks as they arrive

        Returns:
            Final metadata including cost information
        """
        if file_path:
            raise ValueError("LongCatClient does not support file attachments yet.")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text_content or ""},
        ]

        try:
            # Build API parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            
            # Add thinking_budget only for LongCat-Flash-Thinking model
            if thinking_budget is not None and model == "LongCat-Flash-Thinking":
                params["thinking_budget"] = thinking_budget
            
            stream: Any = self.client.chat.completions.create(**params)

            full_response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    full_response += delta
                    yield delta

            input_tokens = self._estimate_tokens(prompt + (text_content or ""))
            output_tokens = self._estimate_tokens(full_response)
            cost = self._estimate_cost(input_tokens, output_tokens)

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
            raise Exception(f"LongCat API error: {str(exc)}") from exc

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)."""
        return len(text) // 4

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on LongCat pricing."""
        input_cost = (input_tokens / 1_000_000) * 0.15  # $0.15 per 1M input tokens
        output_cost = (output_tokens / 1_000_000) * 0.75  # $0.75 per 1M output tokens
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
