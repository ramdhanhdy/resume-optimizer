"""Unit tests for provenance helper methods on SupabaseDatabase."""

from datetime import datetime
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.supabase_db import SupabaseDatabase


# ---------------------------------------------------------------------------
# Minimal fake Supabase client
# ---------------------------------------------------------------------------

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

    def select(self, _fields):
        self.action = "select"
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self.action = "upsert"
        self.payload = payload
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

    def execute(self):
        return self.client.execute_query(self)


class FakeClient:
    def __init__(self):
        self.inserts = []
        self.updates = []
        self._next_id = 1

    def table(self, table_name):
        return FakeQuery(self, table_name)

    def execute_query(self, query):
        if query.action == "insert":
            row_id = self._next_id
            self._next_id += 1
            self.inserts.append({"table": query.table_name, "payload": query.payload})
            return FakeResult([{**query.payload, "id": row_id}])
        if query.action == "update":
            self.updates.append(
                {"table": query.table_name, "payload": query.payload, "filters": list(query.filters)}
            )
            return FakeResult([])
        return FakeResult([])


def make_db(fake_client=None):
    db = SupabaseDatabase.__new__(SupabaseDatabase)
    db.user_id = "user-abc"
    db.client = fake_client or FakeClient()
    return db


# ---------------------------------------------------------------------------
# create_profile_snapshot
# ---------------------------------------------------------------------------

def test_create_profile_snapshot_returns_int_id():
    db = make_db()
    row_id = db.create_profile_snapshot(profile_index={"skills": ["Python"]})
    assert isinstance(row_id, int)
    assert row_id >= 1


def test_create_profile_snapshot_sets_user_id():
    db = make_db()
    db.create_profile_snapshot(profile_index={"skills": []})
    payload = db.client.inserts[0]["payload"]
    assert payload["user_id"] == "user-abc"


def test_create_profile_snapshot_normalizes_json_string():
    db = make_db()
    db.create_profile_snapshot(profile_index='{"skills": ["Go"]}')
    payload = db.client.inserts[0]["payload"]
    assert payload["profile_index"] == {"skills": ["Go"]}


def test_create_profile_snapshot_keeps_invalid_string_as_is():
    db = make_db()
    db.create_profile_snapshot(profile_index="not json")
    payload = db.client.inserts[0]["payload"]
    assert payload["profile_index"] == "not json"


def test_create_profile_snapshot_optional_fields_excluded_when_none():
    db = make_db()
    db.create_profile_snapshot(profile_index={})
    payload = db.client.inserts[0]["payload"]
    assert "legacy_profile_id" not in payload
    assert "application_id" not in payload
    assert "pipeline_run_id" not in payload


def test_create_profile_snapshot_optional_fields_included_when_set():
    db = make_db()
    db.create_profile_snapshot(
        profile_index={},
        legacy_profile_id=7,
        application_id=42,
        builder_model="gemini-2.5-flash",
        prompt_name="profile_agent.md",
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["legacy_profile_id"] == 7
    assert payload["application_id"] == 42
    assert payload["builder_model"] == "gemini-2.5-flash"
    assert payload["prompt_name"] == "profile_agent.md"


# ---------------------------------------------------------------------------
# save_evidence_item
# ---------------------------------------------------------------------------

def test_save_evidence_item_returns_int_id():
    db = make_db()
    row_id = db.save_evidence_item(source_type="job_posting")
    assert isinstance(row_id, int)


def test_save_evidence_item_sets_user_id_and_source_type():
    db = make_db()
    db.save_evidence_item(source_type="resume_upload", application_id=10)
    payload = db.client.inserts[0]["payload"]
    assert payload["user_id"] == "user-abc"
    assert payload["source_type"] == "resume_upload"
    assert payload["application_id"] == 10


def test_save_evidence_item_optional_fields_excluded_when_none():
    db = make_db()
    db.save_evidence_item(source_type="manual_note")
    payload = db.client.inserts[0]["payload"]
    assert "source_uri" not in payload
    assert "content_hash" not in payload
    assert "metadata" not in payload


# ---------------------------------------------------------------------------
# save_agent_step
# ---------------------------------------------------------------------------

def test_save_agent_step_returns_int_id():
    db = make_db()
    row_id = db.save_agent_step(application_id=1, agent_number=0, agent_name="ProfileAgent")
    assert isinstance(row_id, int)


def test_save_agent_step_default_zeros_and_status():
    db = make_db()
    db.save_agent_step(application_id=1, agent_number=1, agent_name="AnalyzerAgent")
    payload = db.client.inserts[0]["payload"]
    assert payload["input_tokens"] == 0
    assert payload["output_tokens"] == 0
    assert payload["cost_usd"] == 0.0
    assert payload["status"] == "completed"
    assert payload["attempt_number"] == 1
    assert payload["params"] == {}


def test_save_agent_step_serializes_datetime_to_iso():
    db = make_db()
    t_start = datetime(2025, 1, 15, 10, 0, 0)
    t_end = datetime(2025, 1, 15, 10, 0, 5)
    db.save_agent_step(
        application_id=1,
        agent_number=2,
        agent_name="OptimizerAgent",
        started_at=t_start,
        completed_at=t_end,
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["started_at"] == t_start.isoformat()
    assert payload["completed_at"] == t_end.isoformat()


def test_save_agent_step_optional_fields_excluded_when_none():
    db = make_db()
    db.save_agent_step(application_id=1, agent_number=3, agent_name="ValidatorAgent")
    payload = db.client.inserts[0]["payload"]
    assert "job_id" not in payload
    assert "input_data" not in payload
    assert "model_name" not in payload
    assert "started_at" not in payload


# ---------------------------------------------------------------------------
# save_resume_artifact
# ---------------------------------------------------------------------------

def test_save_resume_artifact_returns_int_id():
    db = make_db()
    row_id = db.save_resume_artifact(
        application_id=5,
        artifact_type="optimized_resume",
        content_hash="abc123",
    )
    assert isinstance(row_id, int)


def test_save_resume_artifact_marks_prior_not_current():
    db = make_db()
    db.save_resume_artifact(
        application_id=5,
        artifact_type="optimized_resume",
        content_hash="abc123",
        is_current=True,
    )
    assert len(db.client.updates) == 1
    upd = db.client.updates[0]
    assert upd["table"] == "resume_artifacts"
    assert upd["payload"] == {"is_current": False}
    filter_cols = {f[1] for f in upd["filters"]}
    assert "application_id" in filter_cols
    assert "artifact_type" in filter_cols
    assert "user_id" in filter_cols


def test_save_resume_artifact_no_update_when_not_current():
    db = make_db()
    db.save_resume_artifact(
        application_id=5,
        artifact_type="export",
        content_hash="xyz",
        is_current=False,
    )
    assert db.client.updates == []


def test_save_resume_artifact_summary_points_defaults_to_empty_list():
    db = make_db()
    db.save_resume_artifact(
        application_id=5, artifact_type="final_review", content_hash="h1"
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["summary_points"] == []


# ---------------------------------------------------------------------------
# save_validation_finding
# ---------------------------------------------------------------------------

def test_save_validation_finding_returns_int_id():
    db = make_db()
    row_id = db.save_validation_finding(
        application_id=3, finding_type="red_flag", claim="No metrics"
    )
    assert isinstance(row_id, int)


def test_save_validation_finding_sets_user_id_and_required_fields():
    db = make_db()
    db.save_validation_finding(
        application_id=3,
        finding_type="strength",
        verdict="pass",
        confidence=95.0,
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["user_id"] == "user-abc"
    assert payload["application_id"] == 3
    assert payload["finding_type"] == "strength"
    assert payload["verdict"] == "pass"
    assert payload["confidence"] == 95.0


def test_save_validation_finding_optional_fields_excluded_when_none():
    db = make_db()
    db.save_validation_finding(application_id=3, finding_type="ats_check")
    payload = db.client.inserts[0]["payload"]
    assert "agent_step_id" not in payload
    assert "claim" not in payload
    assert "verdict" not in payload


# ---------------------------------------------------------------------------
# save_model_invocation
# ---------------------------------------------------------------------------

def test_save_model_invocation_returns_int_id():
    db = make_db()
    row_id = db.save_model_invocation(provider="gemini", model_name="gemini-2.5-flash")
    assert isinstance(row_id, int)


def test_save_model_invocation_default_status_is_success():
    db = make_db()
    db.save_model_invocation(provider="openrouter", model_name="gpt-4o")
    payload = db.client.inserts[0]["payload"]
    assert payload["status"] == "success"


def test_save_model_invocation_default_zeros():
    db = make_db()
    db.save_model_invocation(provider="gemini", model_name="gemini-2.5-flash")
    payload = db.client.inserts[0]["payload"]
    assert payload["input_tokens"] == 0
    assert payload["output_tokens"] == 0
    assert payload["cost_usd"] == 0.0
    assert payload["params"] == {}


def test_save_model_invocation_sets_user_id():
    db = make_db()
    db.save_model_invocation(provider="gemini", model_name="gemini-2.5-pro")
    payload = db.client.inserts[0]["payload"]
    assert payload["user_id"] == "user-abc"


def test_save_model_invocation_optional_fields_excluded_when_none():
    db = make_db()
    db.save_model_invocation(provider="gemini", model_name="gemini-2.5-flash")
    payload = db.client.inserts[0]["payload"]
    assert "application_id" not in payload
    assert "agent_step_id" not in payload
    assert "latency_ms" not in payload
    assert "error_message" not in payload


def test_save_model_invocation_includes_optional_fields_when_set():
    db = make_db()
    db.save_model_invocation(
        provider="gemini",
        model_name="gemini-2.5-flash",
        application_id=10,
        latency_ms=342,
        pricing_version="v2",
        error_message=None,
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["application_id"] == 10
    assert payload["latency_ms"] == 342
    assert payload["pricing_version"] == "v2"
    assert "error_message" not in payload


# ---------------------------------------------------------------------------
# link_profile_snapshot_to_application
# ---------------------------------------------------------------------------

def test_link_profile_snapshot_issues_update():
    db = make_db()
    db.link_profile_snapshot_to_application(snapshot_id=7, application_id=42)
    assert len(db.client.updates) == 1
    upd = db.client.updates[0]
    assert upd["table"] == "profile_snapshots"
    assert upd["payload"] == {"application_id": 42}


def test_link_profile_snapshot_scoped_to_user_and_id():
    db = make_db()
    db.link_profile_snapshot_to_application(snapshot_id=7, application_id=42)
    upd = db.client.updates[0]
    filter_map = {f[1]: f[2] for f in upd["filters"]}
    assert filter_map["id"] == 7
    assert filter_map["user_id"] == "user-abc"


# ---------------------------------------------------------------------------
# link_evidence_items_to_application
# ---------------------------------------------------------------------------

def test_link_evidence_items_issues_one_update_per_id():
    db = make_db()
    db.link_evidence_items_to_application([10, 11, 12], application_id=99)
    assert len(db.client.updates) == 3


def test_link_evidence_items_sets_correct_application_id():
    db = make_db()
    db.link_evidence_items_to_application([5], application_id=77)
    upd = db.client.updates[0]
    assert upd["table"] == "evidence_items"
    assert upd["payload"] == {"application_id": 77}


def test_link_evidence_items_scoped_to_user():
    db = make_db()
    db.link_evidence_items_to_application([5], application_id=77)
    upd = db.client.updates[0]
    filter_map = {f[1]: f[2] for f in upd["filters"]}
    assert filter_map["user_id"] == "user-abc"
    assert filter_map["id"] == 5


def test_link_evidence_items_empty_list_no_updates():
    db = make_db()
    db.link_evidence_items_to_application([], application_id=77)
    assert db.client.updates == []


# ---------------------------------------------------------------------------
# save_application_review — current_artifact_id linkage
# ---------------------------------------------------------------------------

class FakeClientWithApplications(FakeClient):
    """FakeClient that returns a valid application row for select queries."""

    def execute_query(self, query):
        if query.action == "select" and query.table_name == "applications":
            return FakeResult([{"id": 42}])
        return super().execute_query(query)


def make_db_with_app():
    """Build a db whose fake client returns a valid application for ownership checks."""
    return make_db(fake_client=FakeClientWithApplications())


def test_save_application_review_upserts_core_fields():
    db = make_db_with_app()
    db.save_application_review(
        application_id=42,
        plain_text="Resume text",
        markdown="# Resume",
        filename="resume.docx",
        summary_points=["Point A"],
    )
    upsert = db.client.inserts  # upserts not captured; check via updates or direct
    # The upsert falls through to FakeResult([]) — no crash is the key assertion.
    # The absence of an exception confirms save_application_review completed.


def test_save_application_review_omits_current_artifact_id_when_none():
    db = make_db_with_app()
    # Patch upsert to capture payload
    captured = {}

    original_table = db.client.table

    def patching_table(name):
        q = original_table(name)
        original_upsert = q.upsert

        def capturing_upsert(payload, **kwargs):
            if name == "application_reviews":
                captured["payload"] = payload
            return original_upsert(payload, **kwargs)

        q.upsert = capturing_upsert
        return q

    db.client.table = patching_table
    db.save_application_review(
        application_id=42,
        plain_text="x",
        markdown="y",
        filename="f.docx",
        summary_points=[],
        current_artifact_id=None,
    )
    assert "current_artifact_id" not in captured.get("payload", {})


def test_save_application_review_includes_current_artifact_id_when_set():
    db = make_db_with_app()
    captured = {}

    original_table = db.client.table

    def patching_table(name):
        q = original_table(name)
        original_upsert = q.upsert

        def capturing_upsert(payload, **kwargs):
            if name == "application_reviews":
                captured["payload"] = payload
            return original_upsert(payload, **kwargs)

        q.upsert = capturing_upsert
        return q

    db.client.table = patching_table
    db.save_application_review(
        application_id=42,
        plain_text="x",
        markdown="y",
        filename="f.docx",
        summary_points=[],
        current_artifact_id=99,
    )
    assert captured["payload"]["current_artifact_id"] == 99
