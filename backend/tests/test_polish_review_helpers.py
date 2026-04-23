"""Unit tests for /api/polish review-building helpers."""

from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import server


def test_resolve_review_source_filename_prefers_request_then_app_then_existing_review():
    assert (
        server._resolve_review_source_filename(
            request_resume_filename="resume.pdf",
            application_data={"resume_filename": "stored.pdf"},
            existing_review={"filename": "review.docx"},
        )
        == "resume.pdf"
    )
    assert (
        server._resolve_review_source_filename(
            request_resume_filename=None,
            application_data={"resume_filename": "stored.pdf"},
            existing_review={"filename": "review.docx"},
        )
        == "stored.pdf"
    )
    assert (
        server._resolve_review_source_filename(
            request_resume_filename=None,
            application_data={},
            existing_review={"filename": "review.docx"},
        )
        == "review.docx"
    )


def test_build_polish_summary_points_uses_extracted_insights_when_available(monkeypatch):
    async def fake_extract_insights(_insights_input, _agent_type, max_insights=4):
        assert max_insights == 4
        return [
            {"message": "New insight 1"},
            {"message": "New insight 2"},
        ]

    monkeypatch.setattr(
        server.insight_extractor, "extract_insights_async", fake_extract_insights
    )

    summary_points = asyncio.run(
        server._build_polish_summary_points("opt_report", "val_report", existing_review=None)
    )

    assert summary_points == [
        "New insight 1",
        "New insight 2",
    ]


def test_build_polish_summary_points_falls_back_to_existing_review(monkeypatch):
    async def fake_extract_insights(_insights_input, _agent_type, max_insights=4):
        assert max_insights == 4
        return []

    monkeypatch.setattr(
        server.insight_extractor, "extract_insights_async", fake_extract_insights
    )

    summary_points = asyncio.run(
        server._build_polish_summary_points(
            "opt_report",
            "val_report",
            existing_review={"summary_points": ["Kept existing insight"]},
        )
    )

    assert summary_points == ["Kept existing insight"]
