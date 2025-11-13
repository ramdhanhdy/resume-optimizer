"""Persistence layer for streaming run metadata and event history."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class RunStore:
    """Wrapper around ApplicationDatabase for run metadata and events."""

    def __init__(self, db):
        self._db = db

    def create_run(self, job_id: str, client_id: str, status: str = "pending") -> None:
        self._db.create_run_metadata(job_id=job_id, client_id=client_id, status=status)

    def update_status(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        application_id: Optional[int] = None,
        last_event_id: Optional[int] = None,
    ) -> None:
        self._db.update_run_metadata(
            job_id=job_id,
            status=status,
            application_id=application_id,
            last_event_id=last_event_id,
        )

    def append_event(self, job_id: str, seq: int, event_dict: Dict[str, Any]) -> None:
        self._db.record_run_event(job_id=job_id, seq=seq, event_dict=event_dict)

    def fetch_events(self, job_id: str, after_event_id: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
        return self._db.get_run_events(job_id=job_id, after_seq=after_event_id, limit=limit)

    def get_last_event_id(self, job_id: str) -> Optional[int]:
        return self._db.get_last_run_event_seq(job_id)

    def get_run_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._db.get_run_metadata(job_id)

    def count_runs_for_client(self, client_id: str) -> int:
        return self._db.count_runs_for_client(client_id)

    def purge_run(self, job_id: str) -> None:
        self._db.purge_run_events(job_id)
