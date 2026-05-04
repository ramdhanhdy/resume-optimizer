"""Tests for uploaded file text extraction."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.file_handler import extract_text_from_file


def test_extract_text_from_csv_formats_rows_as_readable_text(tmp_path):
    csv_path = tmp_path / "linkedin_positions.csv"
    csv_path.write_text(
        "Company,Title,Start Date,End Date\n"
        "Acme,Software Engineer,2021,2023\n"
        "Beta,ML Engineer,2023,Present\n",
        encoding="utf-8",
    )

    text = asyncio.run(extract_text_from_file(str(csv_path)))

    assert "CSV file: linkedin_positions.csv" in text
    assert "Row 1:" in text
    assert "Company: Acme" in text
    assert "Title: Software Engineer" in text
    assert "Row 2:" in text
    assert "Company: Beta" in text
    assert "End Date: Present" in text
