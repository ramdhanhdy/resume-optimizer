# Distributed Streaming Hardening Spec

## 1. Overview

Resume Optimizer’s streaming UX regresses after deployment to Cloud Run + Vercel: the frontend reports completion in under a minute even though the backend pipeline runs for 3–5 minutes. Primary causes:

- Cloud Run ingress buffers Server-Sent Events (SSE) until each chunk crosses roughly 4 KB, so important events (including `done`) flush in bursts.
- `StreamManager.subscribe()` replays the entire in-memory history into a bounded queue while holding its lock; once history exceeds 100 events the replay blocks forever, so reconnects never transition to live streaming.
- All event history and job metadata live inside a single instance’s RAM. Multi-instance deployments lose history, break replay, and route snapshot/polling calls to instances that never saw the job.

This document defines the implementation plan to harden the distributed streaming path so production behavior matches local development.

## 2. Goals and Non-Goals

### Goals

1. Deliver true real-time SSE on Cloud Run (per-event latency under one second).
2. Allow late subscribers and reconnects to receive complete history without deadlocking queues.
3. Persist job state so any instance can serve history and snapshots, enabling horizontal scaling again.
4. Provide a staged rollout that preserves existing public APIs (`/api/pipeline/start`, `/api/jobs/{id}/stream`, `/api/jobs/{id}/snapshot`).

### Non-Goals

- Replacing SSE with WebSockets or third-party push services.
- Implementing new billing or auth controls (covered by Supabase specs).
- Redesigning the frontend beyond the wiring necessary to consume the improved stream.

## 3. Current Pain Points

| Issue | Impact | Evidence |
| --- | --- | --- |
| Sub-4 KB SSE frames | Events flush only when total payload exceeds the ingress buffer, so `done` frequently ships before the UI consumes intermediate updates. | `backend/server.py:1481-1506` pads each frame by ~2 KB. |
| Replay deadlock | `asyncio.Queue(maxsize=100)` fills while replaying >100 events; `await queue.put()` blocks under the lock, so EventSource reconnects never complete and the frontend falls back to mock timers. | Observed “frontend finished early” symptom, code in `backend/src/streaming/manager.py`. |
| Single-instance deployment | `deploy.sh` pins `--min-instances=1 --max-instances=1`, eliminating horizontal scale and still losing history after restarts. | Commit `f7372e1`. |
| No durable state | Snapshot endpoint depends on `_event_history` per instance; polling routed to other instances returns empty state, creating non-deterministic UX. | Production-only failure; not reproducible locally because everything shares one process. |

## 4. Proposed Architecture

### 4.1 Immediate Flush Enforcement

- Pad every SSE frame until the serialized payload exceeds 4 KB. Append repeated comment lines (`":<2048 spaces>\n"`) until the threshold is crossed.
- Document that FastAPI’s `StreamingResponse` already uses chunked transfer encoding; confirm headers remain `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`.
- Add debug log when a frame is below 4 KB so regressions surface during testing.

### 4.2 StreamManager Refactor

- Replace bounded subscriber queues with unbounded (`asyncio.Queue(maxsize=0)`) or an explicit drop-old strategy applied outside the lock.
- Copy `self._event_history[job_id]` while holding `_lock`, release the lock, and only then `await queue.put(event)` to avoid blocking other publishers.
- Track replay cursors: store events as `{id, ts, type, payload}`; when a client presents `Last-Event-ID`, skip already delivered events.
- Add `GET /api/jobs/{job_id}/events?after=<cursor>` to provide the same history for polling fallbacks.

### 4.3 Durable Run Store (Phase 2)

- Introduce `run_metadata` and `run_events` tables (initially backed by SQLite to keep demo costs at zero; plan for Supabase/Postgres later, no Redis/Memorystore).
  - `run_metadata`: `job_id (uuid PK)`, `status`, `application_id`, `created_at`, `updated_at`.
  - `run_events`: `id (bigint PK)`, `job_id`, `seq`, `type`, `payload JSON`, `ts`.
- Extract a `RunStore` interface with implementations for in-memory (tests) and SQLite (production v1).
- On `stream_manager.emit` persist events before fan-out; maintain an in-memory LRU cache per job for the most recent N events (default 100).
- Snapshot endpoint reads from the store rather than the process-local history, enabling multi-instance deployments.

### 4.4 Deployment Strategy

1. **Phase 0 (Hotfix)**: increase padding to guarantee flush, bump queue limits to prevent immediate deadlocks.
2. **Phase 1**: implement non-blocking replay and reconnection support; keep single-instance constraint while validating.
3. **Phase 2**: add durable storage, re-enable multi-instance Cloud Run, wire snapshot/polling to the store.
4. **Phase 3**: add metrics/alerts and remove frontend mock timers once streaming is stable.

## 5. Implementation Plan

### Phase 0 – Flush Patch (1 day)

1. Update `stream_job_events()` to append padding loops until `len(serialized_event) >= 4096`.
2. Add a small regression test or script that inspects emitted frame sizes.
3. Redeploy, then run `curl -N` smoke tests to confirm sub-second delivery.

### Phase 1 – Replay and Backpressure Fix (2–3 days)

1. Switch subscriber queues to unbounded; emit a warning metric when depth exceeds 500 to catch downstream stalls.
2. Replay history outside the lock as described above so no `await` runs while `_lock` is held.
3. Add a configurable `history_limit` (default 500 events per job) and prune the oldest entries when exceeded.
4. Implement `Last-Event-ID` handling: parse from headers, set on outbound SSE frames, and teach the frontend hook to respect it.
5. Update documentation (`DEBUGGING_SSE.md`) with the new behavior.

### Phase 2 – Durable Storage and Multi-Instance (5–7 days)

1. Create migrations for `run_metadata` and `run_events`. Add env var `STREAM_STORE_BACKEND=memory|sqlite|postgres`.
2. Implement `RunStore` with transactional writes (SQLite via `aiosqlite`), plus a simple LRU cache for hot history.
3. Modify `stream_manager.emit` to persist events before notifying subscribers; fall back to cache when available.
4. Update `/api/jobs/{job_id}/snapshot` and the new `/events` endpoint to read from the store.
5. Remove the `--max-instances=1` hack in `deploy.sh`; set `--min-instances=1` and raise `--max-instances` once staging proves healthy.
6. Update `DEPLOYMENT.md` and `.env.example` files with new knobs.

### Phase 3 – Observability and Cleanup (2 days)

1. Emit metrics/logs for frame size, replay duration, queue depth, and persistence latency.
2. Add alerts for replay duration >2 s, queue depth >500, or persistence failures >0.1 %.
3. Remove fallback mock timers in the frontend now that the stream is reliable.

## 6. Testing Strategy

- **Unit tests**: cover stream manager replay logic, queue growth warnings, and persistence adapters.
- **Integration tests**: run uvicorn with the SSE endpoint, simulate clients that subscribe late or reconnect mid-run, and verify they catch up properly.
- **Load tests**: use Locust/k6 to start multiple concurrent jobs while intentionally restarting Cloud Run instances; ensure reconnects replay from the store.
- **Frontend tests**: extend `useProcessingJob` tests to verify `Last-Event-ID` usage and idempotent event handling.

## 7. Rollout Plan

1. Branch `feat/streaming-hardening`.
2. Deploy Phase 0 patch via a canary revision; monitor `event_latency_p95`.
3. After Phase 1, re-enable multiple instances only in staging to validate reconnections.
4. Phase 2: run migrations, flip `STREAM_STORE_BACKEND=sqlite` in Cloud Run, raise `--max-instances` to 3, observe for 24 hours.
5. Maintain a rollback playbook: revert to the previous revision and drop new tables if necessary.

## 8. Open Questions

1. **Resolved:** stay on SQLite (no Redis/Memorystore) because this is a low-traffic private demo and we want zero additional hosting cost. Revisit only if we open access to a wider audience.
2. **Quota implementation:** enforce the “5 free runs” rule by generating a UUID per browser (stored in `localStorage`, sent as `X-Client-Id`), counting runs per `client_id` in `run_metadata`, and rejecting when a client exceeds 5. This avoids IP heuristics and keeps the UX auth-free.
3. How do we redact or minimize PII within streamed `agent_chunk` payloads while still providing useful progress?
4. Should pipeline execution wait for an explicit subscriber ACK (create run → client subscribes → backend starts) to eliminate “fire and forget” races?

## 9. Dependencies

- Cloud Run service accounts will need database credentials once we switch to persistent storage.
- Backend runtime must include `aiosqlite` (and later async Postgres client) in `requirements.txt`.
- Frontend browsers must support EventSource + `Last-Event-ID` (true for modern evergreen browsers).

## 10. Deliverables

- Refactored `backend/src/streaming` module with persistence-aware stream manager.
- Updated deployment tooling (`backend/deploy.sh`, `DEPLOYMENT.md`) removing the single-instance constraint.
- Documentation updates (`README.md`, `DEBUGGING_SSE.md`) referencing this hardening plan.
- Test coverage (unit/integration/load) demonstrating reliable streaming across restarts and multiple instances.
