"""Profile Agent (Step 0): builds an evidence-backed profile index.

Outputs a compact, machine-usable index of skills, roles, and projects from
provided profile text (e.g., LinkedIn), with conservative phrasing and
grounding hooks for later steps.
"""

from __future__ import annotations

from typing import Dict, Any, Generator, Optional, List
import json

from .base import BaseAgent


def _truncate(text: str, max_chars: int) -> str:
    text = text or ""
    return text if len(text) <= max_chars else text[:max_chars] + "..."


class ProfileAgent(BaseAgent):
    """Agent for building persistent profile memory/index."""

    def __init__(self, client):
        super().__init__(
            prompt_file="prompts/profile_agent.md",
            agent_name="Profile Agent",
            client=client,
        )

    def _build_user_prompt(
        self, *, profile_text: str, profile_repos: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Wrap raw profile text with clear boundaries for the model."""
        snippet = _truncate(profile_text, 20_000)
        parts = [
            "Below is <profile_text> extracted from public sources. Build an index per schema.",
            "<profile_text>",
            snippet,
            "</profile_text>",
        ]
        if profile_repos:
            try:
                repos_json = json.dumps(profile_repos, ensure_ascii=False)
            except Exception:
                repos_json = "[]"
            repos_snippet = _truncate(repos_json, 12_000)
            parts += [
                "<repos_json>",
                repos_snippet,
                "</repos_json>",
                "Use repos_json as additional evidence when present.",
            ]
        return "\n".join(parts) + "\n"

    def index_profile(
        self,
        *,
        model: str,
        profile_text: str,
        profile_repos: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        max_tokens: int = 3500,
        thinking_budget: Optional[int] = None,
    ) -> Generator[str, None, Dict[str, Any]]:
        """Create a profile index from aggregated profile text.

        Yields streaming chunks; final return value contains metadata.
        """
        user_prompt = self._build_user_prompt(
            profile_text=profile_text, profile_repos=profile_repos
        )

        return self.run(
            model=model,
            text_content=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
        )
