"""Utility functions for the application."""

from .text_diff import get_text_diff, get_change_summary, highlight_keywords, extract_optimized_resume
from .file_handler import save_uploaded_file, cleanup_temp_file, get_file_icon
from .docx_generator import html_to_docx
from .marked_text_to_docx import parse_marked_text_to_docx
from .execute_docx_code import execute_docx_code

__all__ = [
    "get_text_diff",
    "get_change_summary",
    "highlight_keywords",
    "extract_optimized_resume",
    "save_uploaded_file",
    "cleanup_temp_file",
    "get_file_icon",
    "html_to_docx",
    "parse_marked_text_to_docx",
    "execute_docx_code",
]
