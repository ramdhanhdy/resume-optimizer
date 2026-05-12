"""Tests for the resume upload endpoint."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import server


def test_upload_resume_pdf_uses_local_extraction_without_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    pdf_path = PROJECT_ROOT / "tests" / "test_sample.pdf"

    with TestClient(server.app) as client:
        with pdf_path.open("rb") as handle:
            response = client.post(
                "/api/upload-resume",
                files={"file": (pdf_path.name, handle, "application/pdf")},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "test_sample.pdf"
    assert body["extraction_method"] == "pypdf"
    assert body["length"] > 0
    assert body["text"].strip()
