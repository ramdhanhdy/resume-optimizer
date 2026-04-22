"""Tests for plain text resume DOCX rendering."""

from io import BytesIO
from pathlib import Path
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.plain_text_to_docx import _is_section_heading, plain_text_to_docx


def test_is_section_heading_recognizes_common_titlecase_sections():
    assert _is_section_heading("EXPERIENCE")
    assert _is_section_heading("Experience")
    assert _is_section_heading("Technical Skills")
    assert not _is_section_heading("Software Engineer")
    assert not _is_section_heading("jane@example.com")


def test_contact_block_stops_before_titlecase_section_heading():
    document = Document(
        BytesIO(
            plain_text_to_docx(
                "\n".join(
                    [
                        "Jane Doe",
                        "jane@example.com",
                        "Experience",
                        "- Built APIs",
                    ]
                )
            )
        )
    )

    paragraphs = [paragraph for paragraph in document.paragraphs if paragraph.text.strip()]

    assert paragraphs[0].text == "Jane Doe"
    assert paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert paragraphs[1].text == "jane@example.com"
    assert paragraphs[1].alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert paragraphs[2].text == "Experience"
    assert paragraphs[2].alignment != WD_ALIGN_PARAGRAPH.CENTER
