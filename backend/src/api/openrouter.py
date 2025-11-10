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

from .pricing import get_pricing_manager, TokenUsage, CostBreakdown


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
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Stream completion from OpenRouter API.

        Args:
            prompt: System prompt
            model: Model identifier (e.g., 'anthropic/claude-3.5-sonnet')
            text_content: Text input from user
            file_path: Path to uploaded file
            file_type: MIME type of file
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold (0.0-1.0)
            top_k: Top-k sampling limit
            frequency_penalty: Penalize token frequency (-2.0 to 2.0)
            presence_penalty: Penalize token presence (-2.0 to 2.0)
            seed: Random seed for deterministic outputs
            stop: Stop sequences (string or list of strings)

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
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                "extra_headers": {
                    "HTTP-Referer": "https://github.com/yourusername/resume-optimizer",
                    "X-Title": "Resume Optimizer",
                },
            }
            
            # Add optional parameters if provided
            if top_p is not None:
                params["top_p"] = top_p
            if top_k is not None:
                params["top_k"] = top_k
            if frequency_penalty is not None:
                params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                params["presence_penalty"] = presence_penalty
            if seed is not None:
                params["seed"] = seed
            if stop is not None:
                params["stop"] = stop
            
            stream: Any = self.client.chat.completions.create(**params)

            full_response = ""
            usage_data = None
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    yield content_chunk
                
                # Capture usage data if available in final chunk
                if hasattr(chunk, 'usage') and chunk.usage:
                    usage_data = chunk.usage

            # Extract token usage (actual from API or estimated)
            if usage_data:
                input_tokens = getattr(usage_data, 'prompt_tokens', 0)
                output_tokens = getattr(usage_data, 'completion_tokens', 0)
                total_tokens = getattr(usage_data, 'total_tokens', input_tokens + output_tokens)
            else:
                # Fallback to estimation
                input_tokens = self.pricing_manager.estimate_tokens(prompt + str(text_content or ""))
                output_tokens = self.pricing_manager.estimate_tokens(full_response)
                total_tokens = input_tokens + output_tokens

            # Calculate cost using pricing manager
            usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens
            )
            cost_breakdown = self.pricing_manager.calculate_cost("openrouter", model, usage)
            
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

        except Exception as e:
            raise Exception(f"OpenRouter API error: {str(e)}")

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
        """Get total cost across all requests."""
        return self.total_cost

    def reset_total_cost(self):
        """Reset total cost counter."""
        self.total_cost = 0.0
