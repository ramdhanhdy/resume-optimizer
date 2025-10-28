"""Utility functions for the application."""

from .text_diff import get_text_diff, get_change_summary, highlight_keywords, extract_optimized_resume
from .file_handler import save_uploaded_file, cleanup_temp_file, get_file_icon, extract_text_from_file, is_pdf
from .docx_generator import html_to_docx
from .marked_text_to_docx import parse_marked_text_to_docx
from .execute_docx_code import execute_docx_code
from .resume_diff_parser import generate_resume_diff

__all__ = [
    "get_text_diff",
    "get_change_summary",
    "highlight_keywords",
    "extract_optimized_resume",
    "save_uploaded_file",
    "cleanup_temp_file",
    "get_file_icon",
    "extract_text_from_file",
    "is_pdf",
    "html_to_docx",
    "parse_marked_text_to_docx",
    "execute_docx_code",
    "generate_resume_diff",
]
