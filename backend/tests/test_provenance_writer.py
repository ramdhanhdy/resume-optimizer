"""Unit tests for src/app/services/provenance.py (write_agent_provenance, parse_model_string)."""

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.services.provenance import parse_model_string, write_agent_provenance
from src.database.supabase_db import SupabaseDatabase


# ---------------------------------------------------------------------------
# Reuse minimal fake Supabase client (same pattern as test_provenance_helpers)
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


_SAMPLE_METADATA = {"input_tokens": 120, "output_tokens": 80, "cost": 0.002}
_SAMPLE_INPUT = {"job_posting": "Senior Python Engineer..."}
_SAMPLE_OUTPUT = {"text": "Analysis result here"}


# ---------------------------------------------------------------------------
# parse_model_string
# ---------------------------------------------------------------------------

def test_parse_openrouter_model():
    provider, model = parse_model_string("openrouter::anthropic/claude-3.5-sonnet")
    assert provider == "openrouter"
    assert model == "anthropic/claude-3.5-sonnet"


def test_parse_gemini_model_no_separator():
    provider, model = parse_model_string("gemini-2.5-flash")
    assert provider == "gemini"
    assert model == "gemini-2.5-flash"


def test_parse_claude_model_no_separator():
    provider, model = parse_model_string("claude-3-opus")
    assert provider == "anthropic"
    assert model == "claude-3-opus"


def test_parse_unknown_model():
    provider, model = parse_model_string("some-other-model")
    assert provider == "unknown"
    assert model == "some-other-model"


def test_parse_empty_model_string():
    provider, model = parse_model_string("")
    assert provider == "unknown"
    assert model == "unknown"


def test_parse_double_colon_preserves_full_model_id():
    provider, model = parse_model_string("zenmux::qwen/qwen3-max")
    assert provider == "zenmux"
    assert model == "qwen/qwen3-max"


# ---------------------------------------------------------------------------
# write_agent_provenance — happy path
# ---------------------------------------------------------------------------

def test_write_agent_provenance_returns_step_id():
    db = make_db()
    step_id = write_agent_provenance(
        db,
        app_id=42, job_id="job-uuid-123",
        agent_number=1, agent_name="Job Analyzer",
        model_str="openrouter::claude-3.5-sonnet",
        input_data=_SAMPLE_INPUT,
        output_data=_SAMPLE_OUTPUT,
        metadata=_SAMPLE_METADATA,
    )
    assert isinstance(step_id, int)
    assert step_id >= 1


def test_write_agent_provenance_inserts_agent_step_then_model_invocation():
    db = make_db()
    write_agent_provenance(
        db,
        app_id=42, job_id="job-uuid-123",
        agent_number=1, agent_name="Job Analyzer",
        model_str="openrouter::claude-3.5-sonnet",
        input_data=_SAMPLE_INPUT,
        output_data=_SAMPLE_OUTPUT,
        metadata=_SAMPLE_METADATA,
    )
    assert len(db.client.inserts) == 2
    assert db.client.inserts[0]["table"] == "agent_steps"
    assert db.client.inserts[1]["table"] == "model_invocations"


def test_write_agent_provenance_agent_step_fields():
    db = make_db()
    write_agent_provenance(
        db,
        app_id=42, job_id="job-uuid-123",
        agent_number=2, agent_name="Resume Optimizer",
        model_str="gemini-2.5-flash",
        input_data=_SAMPLE_INPUT,
        output_data=_SAMPLE_OUTPUT,
        metadata=_SAMPLE_METADATA,
    )
    step = db.client.inserts[0]["payload"]
    assert step["application_id"] == 42
    assert step["agent_number"] == 2
    assert step["agent_name"] == "Resume Optimizer"
    assert step["model_provider"] == "gemini"
    assert step["model_name"] == "gemini-2.5-flash"
    assert step["input_tokens"] == 120
    assert step["output_tokens"] == 80
    assert step["cost_usd"] == pytest.approx(0.002)
    assert step["status"] == "completed"


def test_write_agent_provenance_model_invocation_links_to_step():
    db = make_db()
    step_id = write_agent_provenance(
        db,
        app_id=42, job_id="job-uuid-123",
        agent_number=1, agent_name="Job Analyzer",
        model_str="openrouter::anthropic/claude-3.5-sonnet",
        input_data=_SAMPLE_INPUT,
        output_data=_SAMPLE_OUTPUT,
        metadata=_SAMPLE_METADATA,
    )
    inv = db.client.inserts[1]["payload"]
    assert inv["agent_step_id"] == step_id
    assert inv["application_id"] == 42
    assert inv["status"] == "success"


def test_write_agent_provenance_token_defaults_when_metadata_empty():
    db = make_db()
    write_agent_provenance(
        db,
        app_id=1, job_id="j",
        agent_number=3, agent_name="Implementer",
        model_str="openrouter::x",
        input_data={}, output_data={},
        metadata={},
    )
    step = db.client.inserts[0]["payload"]
    assert step["input_tokens"] == 0
    assert step["output_tokens"] == 0
    assert step["cost_usd"] == 0.0


# ---------------------------------------------------------------------------
# write_agent_provenance — non-Supabase db (SQLite fallback)
# ---------------------------------------------------------------------------

class _NoProvenanceDb:
    """Simulates SQLite db adapter that has no save_agent_step method."""
    pass


def test_write_agent_provenance_returns_none_for_unsupported_db():
    result = write_agent_provenance(
        _NoProvenanceDb(),
        app_id=1, job_id="j",
        agent_number=1, agent_name="Job Analyzer",
        model_str="openrouter::x",
        input_data={}, output_data={},
        metadata={},
    )
    assert result is None


# ---------------------------------------------------------------------------
# write_agent_provenance — non-fatal error handling
# ---------------------------------------------------------------------------

class _ErrorDb:
    """Simulates a db that raises on save_agent_step."""
    def save_agent_step(self, **_kwargs):
        raise RuntimeError("DB connection lost")


def test_write_agent_provenance_returns_none_on_error(capsys):
    result = write_agent_provenance(
        _ErrorDb(),
        app_id=1, job_id="j",
        agent_number=1, agent_name="Analyzer",
        model_str="openrouter::x",
        input_data={}, output_data={},
        metadata={},
    )
    assert result is None
    captured = capsys.readouterr()
    assert "Provenance write failed" in captured.out
    assert "non-fatal" in captured.out


# ---------------------------------------------------------------------------
# write_final_review_artifact
# ---------------------------------------------------------------------------

from src.app.services.provenance import write_final_review_artifact


_REVIEW_PLAIN = "John Doe\nSenior Engineer\n\nEXPERIENCE\nBuilt scalable systems."
_REVIEW_MARKDOWN = "# John Doe\n## Senior Engineer\n\n## Experience\nBuilt scalable systems."


def test_write_final_review_artifact_returns_int_id():
    db = make_db()
    artifact_id = write_final_review_artifact(
        db,
        app_id=10,
        plain_text=_REVIEW_PLAIN,
        markdown=_REVIEW_MARKDOWN,
    )
    assert isinstance(artifact_id, int)
    assert artifact_id >= 1


def test_write_final_review_artifact_inserts_final_review_type():
    db = make_db()
    write_final_review_artifact(
        db,
        app_id=10,
        plain_text=_REVIEW_PLAIN,
        markdown=_REVIEW_MARKDOWN,
    )
    insert = db.client.inserts[0]
    assert insert["table"] == "resume_artifacts"
    assert insert["payload"]["artifact_type"] == "final_review"
    assert insert["payload"]["is_current"] is True


def test_write_final_review_artifact_computes_content_hash():
    import hashlib
    db = make_db()
    write_final_review_artifact(
        db,
        app_id=10,
        plain_text=_REVIEW_PLAIN,
        markdown=_REVIEW_MARKDOWN,
    )
    expected = hashlib.sha256((_REVIEW_PLAIN + "\n" + _REVIEW_MARKDOWN).encode()).hexdigest()
    payload = db.client.inserts[0]["payload"]
    assert payload["content_hash"] == expected


def test_write_final_review_artifact_marks_prior_as_not_current():
    db = make_db()
    write_final_review_artifact(
        db,
        app_id=10,
        plain_text=_REVIEW_PLAIN,
        markdown=_REVIEW_MARKDOWN,
    )
    assert len(db.client.updates) == 1
    upd = db.client.updates[0]
    assert upd["table"] == "resume_artifacts"
    assert upd["payload"] == {"is_current": False}
    filter_cols = {f[1] for f in upd["filters"]}
    assert "application_id" in filter_cols
    assert "artifact_type" in filter_cols


def test_write_final_review_artifact_passes_agent_step_id():
    db = make_db()
    write_final_review_artifact(
        db,
        app_id=10,
        plain_text=_REVIEW_PLAIN,
        markdown=_REVIEW_MARKDOWN,
        agent_step_id=77,
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["agent_step_id"] == 77


def test_write_final_review_artifact_passes_filename_and_summary():
    db = make_db()
    write_final_review_artifact(
        db,
        app_id=10,
        plain_text=_REVIEW_PLAIN,
        markdown=_REVIEW_MARKDOWN,
        filename="resume.docx",
        summary_points=["Strong Python skills", "Led 3 teams"],
    )
    payload = db.client.inserts[0]["payload"]
    assert payload["filename"] == "resume.docx"
    assert payload["summary_points"] == ["Strong Python skills", "Led 3 teams"]


def test_write_final_review_artifact_returns_none_for_unsupported_db():
    result = write_final_review_artifact(
        _NoProvenanceDb(),
        app_id=1,
        plain_text="x",
        markdown="x",
    )
    assert result is None


def test_write_final_review_artifact_returns_none_on_error(capsys):
    class _ArtifactErrorDb:
        def save_resume_artifact(self, **_kwargs):
            raise RuntimeError("write failed")

    result = write_final_review_artifact(
        _ArtifactErrorDb(),
        app_id=1,
        plain_text="x",
        markdown="x",
    )
    assert result is None
    captured = capsys.readouterr()
    assert "Artifact persistence failed" in captured.out
    assert "non-fatal" in captured.out
