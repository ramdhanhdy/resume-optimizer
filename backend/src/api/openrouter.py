"""OpenRouter API client with streaming support and cost tracking."""

import base64
import os
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Sequence,
    TypedDict,
    Union,
)

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


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key. If not provided, reads from env.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided")

        self.client: Any = OpenAI(
            base_url="https://openrouter.ai/api/v1",
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
            file_path: Path to uploaded file
            file_type: MIME type of file

        Returns:
            List of content items for API
        """
        content: List[ContentPartParam] = []

        if text:
            content.append({"type": "text", "text": text})

        if file_path and file_type:
            # For images
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
            # For PDFs and documents - send as text with instruction
            else:
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
        prompt: str,
        model: str,
        text_content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from OpenRouter API.

        Args:
            prompt: System prompt
            model: Model identifier (e.g., 'anthropic/claude-3.5-sonnet')
            text_content: Text input from user
            file_path: Path to uploaded file
            file_type: MIME type of file
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

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
            stream: Any = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                extra_headers={
                    "HTTP-Referer": "https://github.com/yourusername/resume-optimizer",
                    "X-Title": "Resume Optimizer",
                },
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    yield content_chunk

            # Estimate cost (rough approximation based on token usage)
            # OpenRouter provides this in response headers, but for streaming
            # we'll estimate based on common pricing
            input_tokens = self._estimate_tokens(prompt + str(text_content))
            output_tokens = self._estimate_tokens(full_response)

            # Rough cost estimation (will vary by model)
            cost = self._estimate_cost(model, input_tokens, output_tokens)
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
            raise Exception(f"OpenRouter API error: {str(e)}")

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def _estimate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost based on model and token usage.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Rough pricing estimates per million tokens
        pricing = {
            "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
            "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "openai/gpt-4o": {"input": 5.0, "output": 15.0},
            "google/gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free
            "meta-llama/llama-3.3-70b-instruct": {"input": 0.5, "output": 0.8},
        }

        # Default pricing if model not in list
        default_price = {"input": 1.0, "output": 2.0}
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
