"""Safety checks for LLM-generated DOCX Python templates using gpt-oss-safeguard-20b.

This module integrates the OpenAI gpt-oss-safeguard-20b safety reasoning model
via OpenRouter to classify generated Python code before it is executed in the
DOCX export sandbox.

The safeguard is **opt-in** and controlled by the DOCX_SAFEGUARD_ENABLED
environment variable. When disabled or misconfigured, the existing AST-based
sandbox remains the only line of defense.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional

from openai import OpenAI
from src.utils.prompt_loader import load_prompt


DOCX_SAFEGUARD_ENABLED = os.getenv("DOCX_SAFEGUARD_ENABLED", "false").lower() == "true"
DOCX_SAFEGUARD_MODEL = os.getenv("DOCX_SAFEGUARD_MODEL", "openai/gpt-oss-safeguard-20b")


# Policy tailored for DOCX template Python code safety in this app.
_DOCX_CODE_POLICY = load_prompt("docx_safeguard_policy.md")


_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Get or initialize the OpenRouter OpenAI client.

    Raises when the OPENROUTER_API_KEY is missing.
    """
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required for DOCX safeguard but is not set."
        )

    _client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    return _client


def _classify_docx_code_sync(code: str) -> Dict[str, Any]:
    """Synchronously classify DOCX Python code according to the policy.

    This is intended to be run in a thread via asyncio.to_thread.
    """
    if not code.strip():
        return {
            "label": "UNSAFE",
            "reasoning": "Empty or whitespace-only code cannot be executed.",
            "violations": ["Empty or whitespace-only code"],
        }

    client = _get_client()

    messages = [
        {
            "role": "system",
            "content": _DOCX_CODE_POLICY,
        },
        {
            "role": "user",
            "content": code,
        },
    ]

    response = client.chat.completions.create(
        model=DOCX_SAFEGUARD_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("DOCX safeguard model returned empty content.")

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            "DOCX safeguard model returned non-JSON content."
        ) from exc

    return result


async def classify_docx_code_safety(code: str) -> Optional[Dict[str, Any]]:
    """Classify DOCX Python code as SAFE/UNSAFE/REVIEW.

    Returns the parsed model result when the safeguard is enabled. When the
    safeguard is disabled (DOCX_SAFEGUARD_ENABLED=false), returns None so that
    callers can treat the code as unchecked and rely on other defenses.

    Any runtime errors (missing API key, network issues, etc.) are propagated
    to the caller so they can decide whether to fail open or closed.
    """
    if not DOCX_SAFEGUARD_ENABLED:
        return None

    result = await asyncio.to_thread(_classify_docx_code_sync, code)
    return result


def is_label_safe(result: Dict[str, Any]) -> bool:
    """Return True if the safeguard label is SAFE.

    Treat any unexpected or missing labels as non-safe.
    """
    label = str(result.get("label", "")).upper()
    return label == "SAFE"
