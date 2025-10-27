"""Helper utilities for retrieving web content via Exa."""

from __future__ import annotations

import os
from typing import Any, Iterable, Optional

from exa_py import Exa


class ExaContentError(RuntimeError):
    """Raised when Exa cannot provide requested web content."""


def _validate_urls(urls: Iterable[str]) -> list[str]:
    """Normalize and validate URL inputs."""
    normalized = []
    for url in urls:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("Job posting URL must be a non-empty string.")
        normalized.append(url.strip())
    if not normalized:
        raise ValueError("At least one job posting URL is required.")
    return normalized


def _get_contents_with_fallback(client: Exa, urls: list[str]) -> Any:
    """Call Exa.get_contents with livecrawl fallback.

    Tries livecrawl="always" first (fresh content). If that returns no usable
    results, retries without livecrawl to allow cached content.
    """
    try:
        resp = client.get_contents(urls, text=True, livecrawl="always")
        results = getattr(resp, "results", None)
        if results and getattr(results[0], "text", None):
            return resp
    except Exception:
        # Fall through to cached attempt
        pass

    # Retry without forcing live crawl (cached content may be available)
    return client.get_contents(urls, text=True)


def fetch_job_posting_text(url: str, *, max_chars: Optional[int] = 20_000) -> str:
    """Fetch clean job posting text from Exa's contents endpoint.

    Args:
        url: Public job posting URL.
        max_chars: Optional limit on returned characters to manage downstream cost.

    Returns:
        Parsed text content from the job posting.

    Raises:
        RuntimeError: When the EXA_API_KEY is missing.
        ExaContentError: When Exa fails to return usable content.
        ValueError: When inputs are invalid.
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "EXA_API_KEY is not set. Please add your Exa API key to the environment."
        )

    urls = _validate_urls([url])

    try:
        client = Exa(api_key=api_key)
        response: Any = _get_contents_with_fallback(client, urls)
    except Exception as exc:  # pragma: no cover - network errors are runtime-specific
        raise ExaContentError(
            "Failed to fetch job posting content from Exa. "
            "Verify the URL is accessible and your API key is valid."
        ) from exc

    results = getattr(response, "results", None)
    if not results:
        raise ExaContentError(
            "Exa did not return any content for the provided URL. "
            "The page may require authentication or may not be crawlable."
        )

    first_result = results[0]
    content = getattr(first_result, "text", None)
    if not content:
        raise ExaContentError(
            "Exa returned an empty response for the provided URL. "
            "Try another link or paste the job description manually."
        )

    clean_text = content.strip()
    if not clean_text:
        raise ExaContentError(
            "Exa returned whitespace-only content for the provided URL. "
            "Please verify the page is publicly accessible."
        )

    if max_chars is not None and max_chars > 0 and len(clean_text) > max_chars:
        return clean_text[:max_chars]

    return clean_text


def fetch_public_page_text(url: str, *, max_chars: Optional[int] = 20_000) -> str:
    """Fetch clean text for any public web page via Exa.

    Intended for profile sources (e.g., LinkedIn). Mirrors job posting fetch
    behavior but uses generic wording and can be reused across Step 0.

    Args:
        url: Public URL to fetch
        max_chars: Optional character cap

    Returns:
        Parsed text content.

    Raises:
        RuntimeError: Missing EXA_API_KEY
        ExaContentError: Exa call succeeded but returned unusable content
        ValueError: Invalid inputs
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "EXA_API_KEY is not set. Please add your Exa API key to the environment."
        )

    urls = _validate_urls([url])

    try:
        client = Exa(api_key=api_key)
        response: Any = _get_contents_with_fallback(client, urls)
    except Exception as exc:  # pragma: no cover
        raise ExaContentError(
            "Failed to fetch page content from Exa. Verify the URL and API key."
        ) from exc

    results = getattr(response, "results", None)
    if not results:
        raise ExaContentError("Exa did not return any content for the provided URL.")

    first_result = results[0]
    content = getattr(first_result, "text", None)
    if not content:
        raise ExaContentError("Exa returned an empty response for the provided URL.")

    clean_text = content.strip()
    if not clean_text:
        raise ExaContentError(
            "Exa returned whitespace-only content for the provided URL."
        )

    if max_chars is not None and max_chars > 0 and len(clean_text) > max_chars:
        return clean_text[:max_chars]

    return clean_text


__all__ = ["fetch_job_posting_text", "fetch_public_page_text", "ExaContentError"]
