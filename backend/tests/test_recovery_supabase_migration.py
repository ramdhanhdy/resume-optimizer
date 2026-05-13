import re
from pathlib import Path


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "005_fix_recovery_session_status_constraint.sql"
)


def _migration_sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_recovery_status_migration_allows_backend_statuses():
    sql = _migration_sql()
    allowed_statuses = set(re.findall(r"'([^']+)'", sql))

    assert {
        "pending",
        "processing",
        "failed",
        "recovered",
        "deleted",
    }.issubset(allowed_statuses)


def test_recovery_status_migration_keeps_legacy_statuses_compatible():
    sql = _migration_sql()
    allowed_statuses = set(re.findall(r"'([^']+)'", sql))

    assert {
        "in_progress",
        "expired",
        "abandoned",
    }.issubset(allowed_statuses)


def test_error_log_error_id_migration_accepts_generated_error_ids():
    sql = _migration_sql().lower()

    assert "alter table public.error_logs" in sql
    assert "alter column error_id type text" in sql
    assert "using error_id::text" in sql
