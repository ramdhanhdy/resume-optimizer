"""Zenmux API client with streaming support and basic cost tracking."""

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


class ZenmuxClient:
    """Client for interacting with the Zenmux OpenAI-compatible API."""

    _BASE_URL = "https://zenmux.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ZENMUX_API_KEY")
        if not self.api_key:
            raise ValueError("Zenmux API key not provided")

        self.client: Any = OpenAI(base_url=self._BASE_URL, api_key=self.api_key)

        self.last_request_cost = 0.0
        self.total_cost = 0.0

    def _encode_file(self, file_path: str) -> str:
        with open(file_path, "rb") as file_handle:
            return base64.b64encode(file_handle.read()).decode("utf-8")

    def _prepare_content(
        self,
        text: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> List[ContentPartParam]:
        content: List[ContentPartParam] = []

        if text:
            content.append({"type": "text", "text": text})

        if file_path and file_type:
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
    ) -> Generator[str, None, Dict[str, Any]]:
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
            )

            full_response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    full_response += delta
                    yield delta

            input_tokens = self._estimate_tokens(prompt + (text_content or ""))
            output_tokens = self._estimate_tokens(full_response)
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

        except Exception as exc:  # pragma: no cover - network errors
            raise Exception(f"Zenmux API error: {exc}") from exc

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4 if text else 0

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = {
            "openai/gpt-5": {"input": 20.0, "output": 60.0},
            "anthropic/claude-3.7-sonnet": {"input": 12.0, "output": 36.0},
        }

        default_price = {"input": 5.0, "output": 10.0}
        model_price = pricing.get(model, default_price)

        input_cost = (input_tokens / 1_000_000) * model_price["input"]
        output_cost = (output_tokens / 1_000_000) * model_price["output"]
        return input_cost + output_cost

    def get_last_cost(self) -> float:
        return self.last_request_cost

    def get_total_cost(self) -> float:
        return self.total_cost

    def reset_total_cost(self) -> None:
        self.total_cost = 0.0


__all__ = ["ZenmuxClient"]
