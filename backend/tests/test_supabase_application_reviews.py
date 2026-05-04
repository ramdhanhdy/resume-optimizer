"""Unit tests for Supabase application review ownership handling."""

from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.supabase_db import SupabaseDatabase


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.action = None
        self.filters = []
        self.payload = None
        self.on_conflict = None

    def select(self, _fields):
        self.action = "select"
        return self

    def eq(self, column, value):
        self.filters.append(("eq", column, value))
        return self

    def is_(self, column, value):
        self.filters.append(("is", column, value))
        return self

    def limit(self, _value):
        return self

    def order(self, _column, desc=False):
        return self

    def upsert(self, payload, on_conflict=None):
        self.action = "upsert"
        self.payload = payload
        self.on_conflict = on_conflict
        return self

    def execute(self):
        return self.client.execute_query(self)


class FakeClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.upserts = []

    def table(self, table_name):
        return FakeQuery(self, table_name)

    def execute_query(self, query):
        if query.action == "upsert":
            self.upserts.append(
                {
                    "table": query.table_name,
                    "payload": query.payload,
                    "on_conflict": query.on_conflict,
                }
            )
            return FakeResult([query.payload])

        key = (query.table_name, tuple(query.filters))
        return FakeResult(self.responses.get(key, []))


def make_db(fake_client):
    db = SupabaseDatabase.__new__(SupabaseDatabase)
    db.user_id = "user-1"
    db.client = fake_client
    return db


def test_save_application_review_requires_owned_application():
    db = make_db(FakeClient())

    with pytest.raises(ValueError, match="not found or not owned"):
        db.save_application_review(
            application_id=42,
            plain_text="plain",
            markdown="# review",
            filename="review.docx",
            summary_points=["one"],
        )

    assert db.client.upserts == []


def test_get_application_review_returns_none_when_parent_application_is_missing():
    client = FakeClient(
        responses={
            (
                "application_reviews",
                (("eq", "application_id", 42), ("eq", "user_id", "user-1")),
            ): [
                {
                    "application_id": 42,
                    "user_id": "user-1",
                    "plain_text": "plain",
                    "markdown": "# review",
                    "filename": "review.docx",
                    "summary_points": '["one"]',
                }
            ],
        }
    )
    db = make_db(client)

    assert db.get_application_review(42) is None


def test_get_application_review_normalizes_summary_points_and_status():
    client = FakeClient(
        responses={
            (
                "application_reviews",
                (("eq", "application_id", 42), ("eq", "user_id", "user-1")),
            ): [
                {
                    "application_id": 42,
                    "user_id": "user-1",
                    "plain_text": "plain",
                    "markdown": "# review",
                    "filename": "review.docx",
                    "summary_points": '["one", "two"]',
                }
            ],
            (
                "applications",
                (("eq", "id", 42), ("eq", "user_id", "user-1"), ("is", "deleted_at", "null")),
            ): [{"id": 42, "status": "processing"}],
        }
    )
    db = make_db(client)

    review = db.get_application_review(42)
    assert review is not None
    assert review["status"] == "processing"
    assert review["summary_points"] == ["one", "two"]


def test_get_latest_completed_application_with_review_returns_first_reviewed_app():
    client = FakeClient(
        responses={
            (
                "applications",
                (
                    ("eq", "user_id", "user-1"),
                    ("eq", "status", "completed"),
                    ("is", "deleted_at", "null"),
                ),
            ): [{"id": 43}, {"id": 42}],
            (
                "application_reviews",
                (("eq", "application_id", 43), ("eq", "user_id", "user-1")),
            ): [],
            (
                "application_reviews",
                (("eq", "application_id", 42), ("eq", "user_id", "user-1")),
            ): [
                {
                    "application_id": 42,
                    "user_id": "user-1",
                    "plain_text": "plain",
                    "markdown": "# review",
                    "filename": "review.docx",
                    "summary_points": ["one"],
                }
            ],
            (
                "applications",
                (("eq", "id", 42), ("eq", "user_id", "user-1"), ("is", "deleted_at", "null")),
            ): [{"id": 42, "status": "completed"}],
        }
    )
    db = make_db(client)

    review = db.get_latest_completed_application_with_review()
    assert review is not None
    assert review["application_id"] == 42
    assert review["status"] == "completed"
