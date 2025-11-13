"""Stream manager for handling SSE connections and event broadcasting."""

import asyncio
import json
import threading
from typing import Dict, Set, Optional
from collections import defaultdict
from .events import ProcessingEvent, HeartbeatEvent, DoneEvent


class StreamManager:
    """Manages SSE streams for multiple jobs."""
    
    def __init__(self):
        # job_id -> set of queues
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        # job_id -> list of events (for snapshot/replay)
        self._event_history: Dict[str, list] = defaultdict(list)
        # job_id -> job status
        self._job_status: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._loop = None  # Will be set to main event loop
    
    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific job.
        
        IMPORTANT: Replays all historical events before subscribing to live events.
        This fixes the race condition where frontend connects to SSE after pipeline
        has already emitted initial events (job_status:started, application_id, etc).
        """
        queue = asyncio.Queue(maxsize=100)
        
        async with self._lock:
            # REPLAY: Send all historical events to catch up late subscribers
            for event_dict in self._event_history.get(job_id, []):
                try:
                    # Reconstruct event from stored dict based on 'type' field
                    event_type = event_dict.get('type')
                    
                    # Map event type to class and reconstruct
                    if event_type == 'job_status':
                        from .events import JobStatusEvent
                        event = JobStatusEvent(**event_dict)
                    elif event_type == 'step_progress':
                        from .events import StepProgressEvent
                        event = StepProgressEvent(**event_dict)
                    elif event_type == 'insight_emitted':
                        from .events import InsightEvent
                        event = InsightEvent(**event_dict)
                    elif event_type == 'metric_update':
                        from .events import MetricUpdateEvent
                        event = MetricUpdateEvent(**event_dict)
                    elif event_type == 'validation_update':
                        from .events import ValidationUpdateEvent
                        event = ValidationUpdateEvent(**event_dict)
                    elif event_type == 'agent_step_started':
                        from .events import AgentStepStartedEvent
                        event = AgentStepStartedEvent(**event_dict)
                    elif event_type == 'agent_step_completed':
                        from .events import AgentStepCompletedEvent
                        event = AgentStepCompletedEvent(**event_dict)
                    elif event_type == 'agent_chunk':
                        from .events import AgentChunkEvent
                        event = AgentChunkEvent(**event_dict)
                    elif event_type == 'heartbeat':
                        from .events import HeartbeatEvent
                        event = HeartbeatEvent(**event_dict)
                    elif event_type == 'done':
                        from .events import DoneEvent
                        event = DoneEvent(**event_dict)
                    elif event_type == 'error':
                        from .events import ErrorEvent
                        event = ErrorEvent(**event_dict)
                    else:
                        # Unknown event type, skip
                        print(f"⚠️ Unknown event type for replay: {event_type}")
                        continue
                    
                    # Add to queue (non-blocking since we're filling an empty queue)
                    await queue.put(event)
                    
                except Exception as e:
                    # Log but don't fail subscription on replay errors
                    print(f"⚠️ Failed to replay event for job {job_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # SUBSCRIBE: Add to live subscribers after replay completes
            self._subscribers[job_id].add(queue)
        
        return queue
    
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
            # Store in history
            self._event_history[job_id].append(event.model_dump())
            
            # Update job status cache
            if event.type == "job_status":
                self._job_status[job_id] = event.payload
            
            # Broadcast to subscribers
            if job_id in self._subscribers:
                dead_queues = set()
                for queue in self._subscribers[job_id]:
                    try:
                        queue.put_nowait(event)
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
            status = self._job_status.get(job_id, {"status": "unknown"})
            
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
                        queue.put_nowait(DoneEvent(job_id=job_id))
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


# Global stream manager instance
stream_manager = StreamManager()
