"""Tests for run-store usage accounting behavior."""

import pytest

from src.streaming.run_store import RoutingRunStore, RunStorePersistenceError


def _persistent_client(_client_id: str) -> bool:
    return True


def test_persistent_create_run_fails_closed_when_database_write_fails():
    def failing_db_factory(_client_id: str):
        raise RuntimeError("database unavailable")

    store = RoutingRunStore(
        db_factory=failing_db_factory,
        should_use_persistent_client=_persistent_client,
    )

    with pytest.raises(RunStorePersistenceError):
        store.create_run(job_id="job-1", client_id="user-1", status="queued")


def test_persistent_count_fails_closed_instead_of_falling_back_to_memory():
    def failing_db_factory(_client_id: str):
        raise RuntimeError("database unavailable")

    store = RoutingRunStore(
        db_factory=failing_db_factory,
        should_use_persistent_client=_persistent_client,
    )

    with pytest.raises(RunStorePersistenceError):
        store.count_runs_for_client("user-1")


def test_non_persistent_count_still_uses_memory_store():
    store = RoutingRunStore(
        db_factory=lambda _client_id: None,
        should_use_persistent_client=lambda _client_id: False,
    )

    store.create_run(job_id="job-1", client_id="local-user", status="queued")

    assert store.count_runs_for_client("local-user") == 1
