"""Parallel insight listener for on-the-fly extraction from agent chunks."""

import asyncio
import hashlib
import time
from collections import deque, OrderedDict
from typing import Dict, List, Optional

from .manager import stream_manager
from .events import (
    ProcessingEvent,
    AgentChunkEvent,
    AgentStepCompletedEvent,
    InsightEvent,
    DoneEvent,
)
from .insight_extractor import insight_extractor


class LRUCache:
    """Simple LRU cache for deduplication."""
    
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> bool:
        if key in self.cache:
            self.cache.move_to_end(key)
            return True
        return False
    
    def put(self, key: str):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            self.cache[key] = True


class InsightListener:
    """Listens to agent chunks and extracts insights in real-time."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        
        # Per-step rolling buffer (last N chars)
        self.step_buffers: Dict[str, deque] = {}
        self.buffer_max_size = 5000  # Max chars per step buffer
        
        # Throttling and rate limiting
        self.last_extraction_time: Dict[str, float] = {}
        self.min_extraction_interval = 3.0  # seconds (increased from 1.5 to reduce rate)
        self.min_chunk_size = 800  # chars (increased from 500 to wait for more content)
        
        # Deduplication cache
        self.seen_insights = LRUCache(maxsize=200)
        self.insight_counter = 0
        
        # Agent type mapping
        self.agent_type_map = {
            "Job Analyzer": "analyzer",
            "Resume Optimizer": "optimizer", 
            "Optimizer Implementer": "implementer",
            "Validator": "validator",
            "Polish Agent": "polish"
        }
    
    async def run(self):
        """Main listener loop."""
        print(f"🔍 Starting insight listener for job {self.job_id}")
        
        # Subscribe to all events for this job
        queue = await stream_manager.subscribe(self.job_id)
        
        try:
            while True:
                try:
                    # Wait for event with timeout for periodic cleanup
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    if event.type == "agent_chunk":
                        await self._handle_chunk_event(event)
                    elif event.type == "agent_step_completed":
                        await self._handle_step_completed(event)
                    elif event.type == "done":
                        print(f"🔍 Insight listener stopping for job {self.job_id}")
                        break
                        
                except asyncio.TimeoutError:
                    # Periodic cleanup of old step buffers
                    await self._cleanup_old_steps()
                    
        finally:
            await stream_manager.unsubscribe(self.job_id, queue)
    
    async def _handle_chunk_event(self, event: AgentChunkEvent):
        """Handle incoming agent chunk event."""
        step = event.payload["step"]
        chunk = event.payload["chunk"]
        total_len = event.payload["total_len"]
        
        # Get or create buffer for this step
        if step not in self.step_buffers:
            self.step_buffers[step] = deque(maxlen=self.buffer_max_size)
        
        buffer = self.step_buffers[step]
        buffer.append(chunk)
        
        # Check if we should extract insights
        current_time = time.time()
        last_time = self.last_extraction_time.get(step, 0)
        time_elapsed = current_time - last_time
        
        # Extract if enough time passed OR enough content accumulated
        window_text = ''.join(buffer)
        should_extract = (
            time_elapsed >= self.min_extraction_interval and
            len(window_text) >= self.min_chunk_size
        )
        
        if should_extract:
            await self._extract_insights_for_step(step, window_text)
            self.last_extraction_time[step] = current_time
    
    async def _handle_step_completed(self, event: AgentStepCompletedEvent):
        """Handle step completion - cleanup without re-extraction.
        
        We skip final extraction here because we've already been extracting
        insights continuously during streaming. Re-analyzing the same content
        often produces duplicate insights with slight variations that bypass
        deduplication.
        """
        step = event.payload["step"]
        
        # Clean up the buffer for this step to free memory
        if step in self.step_buffers:
            del self.step_buffers[step]
        if step in self.last_extraction_time:
            del self.last_extraction_time[step]
    
    async def _extract_insights_for_step(self, step: str, text: str):
        """Extract insights from accumulated text for a specific step."""
        try:
            # Determine agent type from step name
            agent_type = self._map_step_to_agent_type(step)
            if not agent_type:
                return
            
            # Use a sliding window of the last N chars for extraction
            # This gives more recent context which is more relevant
            extraction_text = text[-3000:] if len(text) > 3000 else text
            
            # Extract insights asynchronously
            insights = await insight_extractor.extract_insights_async(
                extraction_text, 
                agent_type, 
                max_insights=2  # Limit to 2 insights per extraction (reduced from 3)
            )
            
            # Emit non-system insights
            for insight in insights:
                insight_id = f"ins-{step}-{self.insight_counter}"
                self.insight_counter += 1
                
                # Create deduplication key
                dedupe_key = self._create_dedupe_key(
                    insight["message"], 
                    insight["category"], 
                    step
                )
                
                # Skip if we've already seen this insight
                if self.seen_insights.get(dedupe_key):
                    continue
                
                # Mark as seen
                self.seen_insights.put(dedupe_key)
                
                # Emit the insight event
                await stream_manager.emit(InsightEvent.create(
                    job_id=self.job_id,
                    insight_id=insight_id,
                    category=insight["category"],
                    importance="high",  # All real-time insights are high importance
                    message=insight["message"][:80],  # Truncate to 80 chars
                    step=step
                ))
                
                print(f"🔍 Emitted insight: {insight['category']} - {insight['message'][:50]}")
            
        except Exception as e:
            print(f"❌ Insight extraction failed for step {step}: {e}")
    
    def _map_step_to_agent_type(self, step: str) -> Optional[str]:
        """Map step name to agent type for insight extraction."""
        step_lower = step.lower()
        
        if "analyz" in step_lower:
            return "analyzer"
        elif "optim" in step_lower or "plan" in step_lower:
            return "optimizer"
        elif "implement" in step_lower or "writ" in step_lower:
            return "implementer"
        elif "valid" in step_lower:
            return "validator"
        elif "polish" in step_lower:
            return "polish"
        
        # Try direct mapping from agent names
        for agent_name, agent_type in self.agent_type_map.items():
            if agent_name.lower() == step_lower:
                return agent_type
        
        return None
    
    def _create_dedupe_key(self, message: str, category: str, step: str) -> str:
        """Create a deduplication key for an insight using fuzzy matching.
        
        Uses the first 5 significant words + category to detect similar insights,
        not just exact duplicates.
        """
        # Normalize message
        normalized = message.lower().strip()
        
        # Extract significant words (longer than 3 chars, excluding common words)
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'will', 'your'}
        words = [w for w in normalized.split() if len(w) > 3 and w not in stop_words]
        
        # Use first 5 significant words as the key base
        key_words = ' '.join(words[:5])
        
        # Include category for grouping similar insights by type
        return hashlib.md5(f"{key_words}|{category}".encode()).hexdigest()
    
    async def _cleanup_old_steps(self):
        """Clean up old step buffers to prevent memory leaks."""
        current_time = time.time()
        steps_to_remove = []
        
        # Remove buffers for steps that haven't been updated in 5 minutes
        for step, last_time in self.last_extraction_time.items():
            if current_time - last_time > 300:  # 5 minutes
                steps_to_remove.append(step)
        
        for step in steps_to_remove:
            if step in self.step_buffers:
                del self.step_buffers[step]
            if step in self.last_extraction_time:
                del self.last_extraction_time[step]
        
        if steps_to_remove:
            print(f"🧹 Cleaned up {len(steps_to_remove)} old step buffers")


async def run_insight_listener(job_id: str) -> None:
    """Run the insight listener for a specific job."""
    listener = InsightListener(job_id)
    await listener.run()
