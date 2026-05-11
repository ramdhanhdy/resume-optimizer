"""Persistence layer for streaming run metadata and event history."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


class RunStorePersistenceError(RuntimeError):
    """Raised when persistent run accounting cannot be completed."""


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


class InMemoryRunStore:
    """Process-local run store used when no file-backed database should be created."""

    def __init__(self):
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def create_run(self, job_id: str, client_id: str, status: str = "pending") -> None:
        now = datetime.utcnow().isoformat()
        self._runs[job_id] = {
            "job_id": job_id,
            "client_id": client_id,
            "status": status,
            "application_id": None,
            "last_event_id": 0,
            "created_at": now,
            "updated_at": now,
        }

    def update_status(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        application_id: Optional[int] = None,
        last_event_id: Optional[int] = None,
    ) -> None:
        if job_id not in self._runs:
            self.create_run(job_id=job_id, client_id="", status=status or "pending")
        run = self._runs[job_id]
        if status is not None:
            run["status"] = status
        if application_id is not None:
            run["application_id"] = application_id
        if last_event_id is not None:
            run["last_event_id"] = last_event_id
        run["updated_at"] = datetime.utcnow().isoformat()

    def append_event(self, job_id: str, seq: int, event_dict: Dict[str, Any]) -> None:
        if job_id not in self._runs:
            self.create_run(job_id=job_id, client_id="", status="pending")

        payload = dict(event_dict)
        payload["event_id"] = seq
        events = self._events[job_id]
        for index, event in enumerate(events):
            if event.get("event_id") == seq:
                events[index] = payload
                break
        else:
            events.append(payload)
            events.sort(key=lambda event: event.get("event_id") or 0)

        self.update_status(job_id, last_event_id=seq)

    def fetch_events(
        self,
        job_id: str,
        after_event_id: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        events = self._events.get(job_id, [])
        if after_event_id is not None:
            events = [
                event for event in events
                if (event.get("event_id") or 0) > after_event_id
            ]
        return [dict(event) for event in events[:limit]]

    def get_last_event_id(self, job_id: str) -> Optional[int]:
        if job_id not in self._runs:
            return None
        last_event_id = self._runs[job_id].get("last_event_id")
        return int(last_event_id) if last_event_id else None

    def get_run_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        run = self._runs.get(job_id)
        return dict(run) if run else None

    def count_runs_for_client(self, client_id: str) -> int:
        return sum(1 for run in self._runs.values() if run.get("client_id") == client_id)

    def purge_run(self, job_id: str) -> None:
        self._events.pop(job_id, None)


class RoutingRunStore:
    """Route run persistence to Supabase when possible, with in-memory fallback."""

    def __init__(self, db_factory, should_use_persistent_client, logger=None):
        self._db_factory = db_factory
        self._should_use_persistent_client = should_use_persistent_client
        self._logger = logger
        self._memory = InMemoryRunStore()
        self._persistent_stores: Dict[str, RunStore] = {}

    def create_run(self, job_id: str, client_id: str, status: str = "pending") -> None:
        self._memory.create_run(job_id=job_id, client_id=client_id, status=status)
        if not self._should_use_persistent_client(client_id):
            return

        try:
            store = RunStore(self._db_factory(client_id))
            store.create_run(job_id=job_id, client_id=client_id, status=status)
            self._persistent_stores[job_id] = store
        except Exception as exc:
            self._log_warning(f"Failed to persist run {job_id}: {exc}")
            raise RunStorePersistenceError(
                f"Failed to persist run metadata for {job_id}"
            ) from exc

    def update_status(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        application_id: Optional[int] = None,
        last_event_id: Optional[int] = None,
    ) -> None:
        self._memory.update_status(
            job_id,
            status=status,
            application_id=application_id,
            last_event_id=last_event_id,
        )
        store = self._persistent_stores.get(job_id)
        if not store:
            return
        try:
            store.update_status(
                job_id,
                status=status,
                application_id=application_id,
                last_event_id=last_event_id,
            )
        except Exception as exc:
            self._log_warning(f"Failed to update persisted run {job_id}: {exc}")

    def append_event(self, job_id: str, seq: int, event_dict: Dict[str, Any]) -> None:
        self._memory.append_event(job_id=job_id, seq=seq, event_dict=event_dict)
        store = self._persistent_stores.get(job_id)
        if not store:
            return
        try:
            store.append_event(job_id=job_id, seq=seq, event_dict=event_dict)
        except Exception as exc:
            self._log_warning(f"Failed to persist run event {job_id}/{seq}: {exc}")

    def fetch_events(
        self,
        job_id: str,
        after_event_id: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        store = self._persistent_stores.get(job_id)
        if store:
            try:
                events = store.fetch_events(
                    job_id,
                    after_event_id=after_event_id,
                    limit=limit,
                )
                if events:
                    return events
            except Exception as exc:
                self._log_warning(f"Failed to fetch persisted events for {job_id}: {exc}")
        return self._memory.fetch_events(
            job_id,
            after_event_id=after_event_id,
            limit=limit,
        )

    def get_last_event_id(self, job_id: str) -> Optional[int]:
        store = self._persistent_stores.get(job_id)
        if store:
            try:
                last_event_id = store.get_last_event_id(job_id)
                if last_event_id is not None:
                    return last_event_id
            except Exception as exc:
                self._log_warning(f"Failed to fetch persisted event sequence for {job_id}: {exc}")
        return self._memory.get_last_event_id(job_id)

    def get_run_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        store = self._persistent_stores.get(job_id)
        if store:
            try:
                metadata = store.get_run_metadata(job_id)
                if metadata:
                    return metadata
            except Exception as exc:
                self._log_warning(f"Failed to fetch persisted run metadata for {job_id}: {exc}")
        return self._memory.get_run_metadata(job_id)

    def count_runs_for_client(self, client_id: str) -> int:
        if self._should_use_persistent_client(client_id):
            try:
                return RunStore(self._db_factory(client_id)).count_runs_for_client(client_id)
            except Exception as exc:
                self._log_warning(f"Failed to count persisted runs for {client_id}: {exc}")
                raise RunStorePersistenceError(
                    f"Failed to count persisted runs for {client_id}"
                ) from exc
        return self._memory.count_runs_for_client(client_id)

    def purge_run(self, job_id: str) -> None:
        self._memory.purge_run(job_id)
        store = self._persistent_stores.get(job_id)
        if not store:
            return
        try:
            store.purge_run(job_id)
        except Exception as exc:
            self._log_warning(f"Failed to purge persisted run {job_id}: {exc}")

    def _log_warning(self, message: str) -> None:
        if self._logger:
            self._logger.warning(message)
