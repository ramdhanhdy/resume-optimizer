"""Helpers for building and serializing the canonical review document."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


def build_review_filename(source_filename: str | None) -> str:
    """Return a deterministic export filename for the reviewed resume."""
    if not source_filename:
        return "optimized-resume.docx"

    candidate = Path(source_filename).name.strip()
    if not candidate:
        return "optimized-resume.docx"

    stem = Path(candidate).stem.strip() or "optimized-resume"
    return f"{stem}.docx"


def normalize_resume_text(resume_text: str) -> str:
    """Normalize line endings and trim noisy leading/trailing whitespace."""
    lines = [line.rstrip() for line in resume_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    normalized: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and previous_blank:
            continue
        normalized.append(line)
        previous_blank = blank

    return "\n".join(normalized).strip()


def resume_text_to_markdown(resume_text: str) -> str:
    """Best-effort markdown representation derived from plain resume text."""
    normalized = normalize_resume_text(resume_text)
    if not normalized:
        return ""

    lines = normalized.split("\n")
    markdown_lines: list[str] = []
    first_non_empty = True

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            markdown_lines.append("")
            continue

        if first_non_empty:
            markdown_lines.append(f"# {line}")
            first_non_empty = False
            continue

        if _is_section_heading(line):
            markdown_lines.append(f"## {line.title()}")
            continue

        if _is_bullet_line(line):
            markdown_lines.append(f"- {_strip_bullet_prefix(line)}")
            continue

        markdown_lines.append(line)

    return "\n".join(markdown_lines).strip()


def build_review_document(
    *,
    application_id: int,
    status: str,
    resume_text: str,
    summary_points: Iterable[str] | None = None,
    source_filename: str | None = None,
) -> dict[str, Any]:
    """Build the canonical review document payload persisted by the backend."""
    plain_text = normalize_resume_text(resume_text)
    cleaned_points = [
        point.strip()
        for point in (summary_points or [])
        if isinstance(point, str) and point.strip()
    ]

    return {
        "application_id": application_id,
        "status": status,
        "plain_text": plain_text,
        "markdown": resume_text_to_markdown(plain_text),
        "filename": build_review_filename(source_filename),
        "summary_points": cleaned_points,
    }


def serialize_review_payload(
    review_document: dict[str, Any],
    *,
    docx_url: str | None = None,
    pdf_url: str | None = None,
) -> dict[str, Any]:
    """Map persisted review data to the frontend review payload contract."""
    return {
        "application_id": review_document["application_id"],
        "status": review_document.get("status", "completed"),
        "resume": {
            "filename": review_document["filename"],
            "plain_text": review_document.get("plain_text", ""),
            "markdown": review_document.get("markdown", ""),
        },
        "summary_points": list(review_document.get("summary_points") or []),
        "exports": {
            "docx_url": docx_url,
            "pdf_url": pdf_url,
        },
    }


def _is_section_heading(line: str) -> bool:
    if len(line) > 60:
        return False
    if any(ch.isdigit() for ch in line):
        return False
    if "@" in line or "http" in line.lower():
        return False
    alpha = [ch for ch in line if ch.isalpha()]
    return bool(alpha) and line == line.upper()


def _is_bullet_line(line: str) -> bool:
    return line.startswith(("•", "-", "*"))


def _strip_bullet_prefix(line: str) -> str:
    return line[1:].strip() if _is_bullet_line(line) else line
