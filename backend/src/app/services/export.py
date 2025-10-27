"""Export helpers for rendering files from model outputs."""
from typing import Optional
from html import escape as _html_escape

from src.agents import RendererAgent
from src.utils import html_to_docx as _html_to_docx
from src.utils import execute_docx_code as _execute_docx_code


def generate_pdf_from_html(html: str) -> bytes:
    renderer = RendererAgent()
    return renderer.to_pdf_from_html(html)


def generate_docx_from_html(html: str) -> bytes:
    return _html_to_docx(html)


def generate_docx_from_code(code: str) -> bytes:
    """Generate DOCX from LLM code output with graceful fallback.

    Tries to execute provided Python code in a sandbox. If parsing/execution fails,
    surfaces the underlying error so callers can correct the generated code instead
    of silently receiving an empty document.
    """
    try:
        return _execute_docx_code(code)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Generated DOCX code failed: {exc}") from exc
