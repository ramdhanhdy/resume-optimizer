"""Tests for latest completed review restore endpoint."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import server


class DummyReviewDb:
    def __init__(self, review=None):
        self.review = review

    def get_latest_completed_application_with_review(self):
        return self.review

    def get_application_review(self, application_id):
        if self.review and self.review["application_id"] == application_id:
            return self.review
        return None


def _review(application_id=42):
    return {
        "application_id": application_id,
        "plain_text": "plain resume",
        "markdown": "# resume",
        "filename": "resume.docx",
        "summary_points": ["one", "two"],
        "status": "completed",
    }


def test_latest_review_endpoint_returns_canonical_payload(monkeypatch):
    dummy_db = DummyReviewDb(_review())
    monkeypatch.setattr(server, "get_db_for_user", lambda user_id: dummy_db)
    server.app.dependency_overrides[server.require_user_data_user_id] = lambda: "user-1"

    try:
        response = TestClient(server.app).get("/api/applications/latest-review")
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["review"] == {
        "application_id": 42,
        "status": "completed",
        "resume": {
            "filename": "resume.docx",
            "plain_text": "plain resume",
            "markdown": "# resume",
        },
        "summary_points": ["one", "two"],
        "exports": {
            "docx_url": "/api/export/42?format=docx",
            "pdf_url": None,
        },
    }


def test_latest_review_endpoint_returns_404_when_none(monkeypatch):
    monkeypatch.setattr(server, "get_db_for_user", lambda user_id: DummyReviewDb())
    server.app.dependency_overrides[server.require_user_data_user_id] = lambda: "user-1"

    try:
        response = TestClient(server.app).get("/api/applications/latest-review")
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 404
