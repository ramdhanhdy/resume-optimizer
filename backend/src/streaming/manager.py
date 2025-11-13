"""Stream manager for handling SSE connections and event broadcasting."""

import asyncio
import os
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Set, Optional, List, TYPE_CHECKING

from .events import (
    ProcessingEvent,
    HeartbeatEvent,
    DoneEvent,
    JobStatusEvent,
    StepProgressEvent,
    InsightEvent,
    MetricUpdateEvent,
    ValidationUpdateEvent,
    DiffChunkEvent,
    ErrorEvent,
    AgentStepStartedEvent,
    AgentStepCompletedEvent,
    AgentChunkEvent,
)

if TYPE_CHECKING:
    from .run_store import RunStore


@dataclass
class StreamQueueItem:
    """Envelope containing an event and its sequential ID."""
    event: ProcessingEvent
    event_id: int


class StreamManager:
    """Manages SSE streams for multiple jobs."""
    
    def __init__(self):
        # job_id -> set of queues
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        # job_id -> list of events (for snapshot/replay)
        self._event_history: Dict[str, list] = defaultdict(list)
        self._event_seq: Dict[str, int] = defaultdict(int)
        # job_id -> job status
        self._job_status: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._loop = None  # Will be set to main event loop
        self._history_limit = int(os.getenv("STREAM_HISTORY_LIMIT", "500"))
        self._store: Optional["RunStore"] = None
        self._event_type_map = {
            "job_status": JobStatusEvent,
            "step_progress": StepProgressEvent,
            "insight_emitted": InsightEvent,
            "metric_update": MetricUpdateEvent,
            "validation_update": ValidationUpdateEvent,
            "diff_chunk": DiffChunkEvent,
            "error": ErrorEvent,
            "heartbeat": HeartbeatEvent,
            "done": DoneEvent,
            "agent_step_started": AgentStepStartedEvent,
            "agent_step_completed": AgentStepCompletedEvent,
            "agent_chunk": AgentChunkEvent,
        }
    
    def attach_store(self, store: "RunStore") -> None:
        """Attach persistent run store."""
        self._store = store

    async def subscribe(self, job_id: str, after_event_id: Optional[int] = None) -> asyncio.Queue:
        """Subscribe to events for a specific job.
        
        IMPORTANT: Replays all historical events before subscribing to live events.
        This fixes the race condition where frontend connects to SSE after pipeline
        has already emitted initial events (job_status:started, application_id, etc).
        """
        queue: asyncio.Queue = asyncio.Queue()
        
        async with self._lock:
            history_snapshot: List[dict] = list(self._event_history.get(job_id, []))
            if not history_snapshot:
                history_snapshot = self._load_history_locked(job_id)
            self._subscribers[job_id].add(queue)
        
        replay_items: List[StreamQueueItem] = []
        for event_dict in history_snapshot:
            event_id = event_dict.get("event_id")
            if after_event_id is not None and event_id is not None:
                if event_id <= after_event_id:
                    continue
            envelope = self._deserialize_event(event_dict)
            if envelope:
                replay_items.append(envelope)
        
        for envelope in replay_items:
            try:
                await queue.put(envelope)
            except Exception as exc:
                print(f"⚠️ Failed to enqueue replay event for job {job_id}: {exc}")
        
        return queue

    def _deserialize_event(self, event_dict: dict) -> Optional[StreamQueueItem]:
        """Convert stored event dict back into a queue envelope."""
        try:
            event_type = event_dict.get("type")
            event_cls = self._event_type_map.get(event_type)
            if not event_cls:
                print(f"⚠️ Unknown event type for replay: {event_type}")
                return None
            payload = dict(event_dict)
            event_id = payload.pop("event_id", None)
            event = event_cls(**payload)
            return StreamQueueItem(event=event, event_id=event_id or 0)
        except Exception as exc:
            print(f"⚠️ Failed to deserialize event: {exc}")
            import traceback
            traceback.print_exc()
            return None
    
    async def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        """Unsubscribe from job events."""
        async with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id].discard(queue)
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]
    
    async def emit(self, event: ProcessingEvent):
        """Emit an event to all subscribers of a job."""
        job_id = event.job_id
        
        async with self._lock:
            self._ensure_event_seq_locked(job_id)
            self._event_seq[job_id] += 1
            event_seq = self._event_seq[job_id]
            # Store in history
            event_dict = event.model_dump()
            event_dict["event_id"] = event_seq
            history = self._event_history[job_id]
            history.append(event_dict)
            if len(history) > self._history_limit:
                del history[: len(history) - self._history_limit]
            
            # Update job status cache
            if event.type == "job_status":
                self._job_status[job_id] = event.payload
                if self._store:
                    self._store.update_status(job_id, status=event.payload.get("status"))

            if self._store and event.type != "heartbeat":
                self._store.append_event(job_id, event_seq, event_dict)
            
            # Broadcast to subscribers
            if job_id in self._subscribers:
                dead_queues = set()
                envelope = StreamQueueItem(event=event, event_id=event_seq)
                for queue in self._subscribers[job_id]:
                    try:
                        queue.put_nowait(envelope)
                    except asyncio.QueueFull:
                        # Mark for removal if queue is full
                        dead_queues.add(queue)
                
                # Clean up dead queues
                for queue in dead_queues:
                    self._subscribers[job_id].discard(queue)
    
    async def get_snapshot(self, job_id: str) -> dict:
        """Get current snapshot of job state."""
        async with self._lock:
            events = self._event_history.get(job_id, [])
            if not events:
                events = self._load_history_locked(job_id)
            status = self._job_status.get(job_id, {"status": "unknown"})
            if status.get("status") == "unknown" and self._store:
                metadata = self._store.get_run_metadata(job_id)
                if metadata and metadata.get("status"):
                    status = {"status": metadata["status"]}
            
            # Extract recent chunks and insights for the snapshot
            recent_chunks = []
            recent_insights = []
            
            # Limit to last 50 chunks and 20 insights
            chunk_count = 0
            insight_count = 0
            
            # Process events in reverse order (most recent first)
            for event in reversed(events[-100:]):  # Look at last 100 events
                if event["type"] == "agent_chunk" and chunk_count < 50:
                    recent_chunks.append(event)
                    chunk_count += 1
                elif event["type"] == "insight_emitted" and insight_count < 20:
                    recent_insights.append(event)
                    insight_count += 1
            
            # Build snapshot from events
            snapshot = {
                "job_id": job_id,
                "status": status.get("status", "unknown"),
                "events": events,
                "event_count": len(events),
                "recent_chunks": list(reversed(recent_chunks)),  # Chronological order
                "recent_insights": list(reversed(recent_insights)),  # Chronological order
                "chunk_count": chunk_count,
                "insight_count": insight_count,
            }
            
            return snapshot
    
    async def cleanup_job(self, job_id: str, keep_history: bool = True):
        """Clean up job resources."""
        async with self._lock:
            # Close all subscriber queues
            if job_id in self._subscribers:
                for queue in self._subscribers[job_id]:
                    # Send done event
                    try:
                        envelope = StreamQueueItem(
                            event=DoneEvent(job_id=job_id),
                            event_id=self._event_seq.get(job_id, 0),
                        )
                        queue.put_nowait(envelope)
                    except:
                        pass
                del self._subscribers[job_id]
            
            # Optionally clear history
            if not keep_history:
                if job_id in self._event_history:
                    del self._event_history[job_id]
                if job_id in self._job_status:
                    del self._job_status[job_id]
    
    def has_subscribers(self, job_id: str) -> bool:
        """Check if job has active subscribers."""
        return job_id in self._subscribers and len(self._subscribers[job_id]) > 0

    def set_main_loop(self, loop):
        """Set the main event loop for thread-safe emission."""
        self._loop = loop

    def emit_from_thread(self, event: ProcessingEvent) -> None:
        """Emit an event safely from a different thread (e.g., executor thread).
        
        This method is thread-safe and can be called from any thread.
        """
        if self._loop is None:
            # Set to current thread's loop if not already set
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                # Not in an event loop thread, we need the main loop
                return
        
        try:
            # Schedule the async emit on the main loop
            asyncio.run_coroutine_threadsafe(self.emit(event), self._loop)
        except (RuntimeError, AttributeError):
            # Loop is closed or not running, ignore silently
            pass

    def _load_history_locked(self, job_id: str) -> List[dict]:
        """Load history from persistent store while lock is held."""
        if not self._store:
            return []
        events = self._store.fetch_events(job_id)
        if not events:
            return []
        snapshot = [dict(evt) for evt in events]
        self._event_history[job_id] = list(snapshot)
        last_seq = snapshot[-1].get("event_id")
        if last_seq:
            self._event_seq[job_id] = last_seq
        return snapshot

    def _ensure_event_seq_locked(self, job_id: str) -> None:
        """Ensure event sequence counter starts from persisted value."""
        if self._event_seq.get(job_id, 0) > 0:
            return
        if not self._store:
            return
        last_seq = self._store.get_last_event_id(job_id)
        if last_seq:
            self._event_seq[job_id] = last_seq


# Global stream manager instance
stream_manager = StreamManager()
