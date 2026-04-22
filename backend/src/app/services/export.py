"""Export helpers for rendering files from model outputs."""
from src.agents import RendererAgent
from src.utils import html_to_docx as _html_to_docx
from src.utils import plain_text_to_docx as _plain_text_to_docx


def generate_pdf_from_html(html: str) -> bytes:
    renderer = RendererAgent()
    return renderer.to_pdf_from_html(html)


def generate_docx_from_html(html: str) -> bytes:
    return _html_to_docx(html)


def generate_docx_from_plain_text(resume_text: str) -> bytes:
    """Generate DOCX deterministically from plain-text resume content."""
    return _plain_text_to_docx(resume_text)
