"""Cerebras API client with streaming support and cost tracking."""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Generator, List, Literal, Optional, Sequence, TypedDict, Union

from openai import OpenAI


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


class CerebrasClient:
    """Client for interacting with Cerebras Inference API.

    The Cerebras API is OpenAI-compatible and provides high-performance
    inference for models like Qwen 3 235B Instruct and GPT OSS 120B.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Cerebras client.

        Args:
            api_key: Cerebras API key. If not provided, reads from env.
        """
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ValueError("Cerebras API key not provided")

        self.client: Any = OpenAI(
            base_url="https://api.cerebras.ai/v1",
            api_key=self.api_key,
        )

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

    def _prepare_content(
        self,
        text: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> List[ContentPartParam]:
        """Prepare content for API request.

        Args:
            text: Text content
            file_path: Path to uploaded file (text-only models)
            file_type: MIME type of file

        Returns:
            List of content items for API
        """
        content: List[ContentPartParam] = []

        if text:
            content.append({"type": "text", "text": text})

        # Note: Cerebras models currently only support text input
        if file_path and file_type:
            # For documents - send as text with instruction
            content.append(
                {
                    "type": "text",
                    "text": (
                        f"[Document attached: {os.path.basename(file_path)}]"
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
        top_p: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from Cerebras API.

        Args:
            prompt: System prompt
            model: Model identifier (e.g., 'qwen-3-235b-a22b-instruct-2507', 'gpt-oss-120b')
            text_content: Text input from user
            file_path: Path to uploaded file (note: text-only models)
            file_type: MIME type of file
            temperature: Sampling temperature (0.0-1.5)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold (0.0-1.0)
            seed: Random seed for deterministic outputs

        Yields:
            Response chunks as they arrive

        Returns:
            Final metadata including cost information
        """
        content = self._prepare_content(text_content, file_path, file_type)

        messages: List[ChatMessageParam] = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ]

        try:
            # Build parameters with optional values
            params: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": max(0.0, min(1.5, temperature)),  # Cerebras limit
                "max_tokens": max_tokens,
                "stream": True,
            }
            
            # Add optional parameters if provided
            if top_p is not None:
                params["top_p"] = top_p
            if seed is not None:
                params["seed"] = seed
            
            stream: Any = self.client.chat.completions.create(**params)

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    yield content_chunk

            # Calculate cost based on token usage
            input_tokens = self._estimate_tokens(prompt + str(text_content or ""))
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

        except Exception as e:
            raise Exception(f"Cerebras API error: {str(e)}")

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4 if text else 0

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost based on Cerebras pricing.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Cerebras pricing per million tokens
        pricing = {
            "qwen-3-235b-a22b-instruct-2507": {"input": 0.60, "output": 1.20},
            "gpt-oss-120b": {"input": 0.35, "output": 0.75},
            "qwen-3-coder-480b": {"input": 2.00, "output": 2.00},
        }

        # Default pricing if model not in list (use Qwen 235B as default)
        default_price = {"input": 0.60, "output": 1.20}
        model_price = pricing.get(model, default_price)

        input_cost = (input_tokens / 1_000_000) * model_price["input"]
        output_cost = (output_tokens / 1_000_000) * model_price["output"]

        return input_cost + output_cost

    def get_last_cost(self) -> float:
        """Get cost of last request."""
        return self.last_request_cost

    def get_total_cost(self) -> float:
        """Get total cost across all requests."""
        return self.total_cost

    def reset_total_cost(self):
        """Reset total cost counter."""
        self.total_cost = 0.0


__all__ = ["CerebrasClient"]
