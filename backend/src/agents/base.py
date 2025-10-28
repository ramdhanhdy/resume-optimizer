"""Base agent class for all resume optimization agents."""

from pathlib import Path
from typing import Any, Dict, Generator, Optional, Union
import inspect

from src.api import OpenRouterClient, LongCatClient, ZenmuxClient
from src.api.multiprovider import MultiProviderClient
from src.api.types import CompletionRequest, GenerationConfig
from src.api.model_registry import get_api_model

ClientType = Union[OpenRouterClient, LongCatClient, ZenmuxClient]


class BaseAgent:
    """Base class for all agents in the pipeline."""

    def __init__(
        self,
        prompt_file: str,
        agent_name: str,
        client: ClientType,
    ):
        """Initialize base agent.

        Args:
            prompt_file: Path to markdown file containing agent prompt
            agent_name: Name of the agent
            client: API client instance (OpenRouter or LongCat)
        """
        self.agent_name = agent_name
        self.client = client
        self.system_prompt = self._load_prompt(prompt_file)

    def _load_prompt(self, prompt_file: str) -> str:
        """Load system prompt from markdown file."""
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        return prompt_path.read_text(encoding="utf-8")

    def run(
        self,
        *,
        model: str,
        text_content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        thinking_budget: Optional[int] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Execute agent with streaming response."""
        # If using the facade, prefer its DTO-based streaming
        if isinstance(self.client, MultiProviderClient):
            request: CompletionRequest = {
                "system_prompt": self.system_prompt,
                "user_text": text_content,
                "file_path": file_path,
                "file_type": file_type,
                "generation": GenerationConfig(
                    temperature=temperature, max_tokens=max_tokens
                ),
            }
            provider_options: Dict[str, Any] = {}
            if thinking_budget is not None:
                provider_options["thinking_budget"] = thinking_budget
            stream = self.client.stream(
                request,
                model=model,
                provider_options=provider_options or None,
            )
        else:
            # Fallback for direct provider clients: build argument payload and
            # filter to what the client supports to avoid leaking provider-specific kwargs
            api_model = get_api_model(model)
            payload: Dict[str, Any] = {
                "prompt": self.system_prompt,
                "model": api_model,
                "text_content": text_content,
                "file_path": file_path,
                "file_type": file_type,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "thinking_budget": thinking_budget,
            }

            sig = inspect.signature(self.client.stream_completion)
            params = sig.parameters
            accepts_var_kwargs = any(
                p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
            )

            if accepts_var_kwargs:
                filtered = payload
            else:
                allowed = set(params.keys())
                filtered = {k: v for k, v in payload.items() if k in allowed}

            stream = self.client.stream_completion(**filtered)

        # Yield all chunks and capture return value
        try:
            while True:
                chunk = next(stream)
                yield chunk
        except StopIteration as exc:
            return exc.value if exc.value else {}
