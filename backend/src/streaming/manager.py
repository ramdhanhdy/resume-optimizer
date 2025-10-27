"""Stream manager for handling SSE connections and event broadcasting."""

import asyncio
import json
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
    
    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific job."""
        queue = asyncio.Queue(maxsize=100)
        async with self._lock:
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
            
            # Build snapshot from events
            snapshot = {
                "job_id": job_id,
                "status": status.get("status", "unknown"),
                "events": events,
                "event_count": len(events),
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


# Global stream manager instance
stream_manager = StreamManager()
