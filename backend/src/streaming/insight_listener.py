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


# Global in-memory cache for run insights
run_insights_cache: Dict[str, List[Dict]] = {}


def get_run_insights(run_id: str) -> List[Dict]:
    """Get all insights for a run."""
    return run_insights_cache.get(run_id, [])


def cache_insight(run_id: str, insight_text: str, agent_step: str) -> None:
    """Cache an insight for a run."""
    if run_id not in run_insights_cache:
        run_insights_cache[run_id] = []
    
    run_insights_cache[run_id].append({
        "text": insight_text,
        "agent_step": agent_step,
        "timestamp": time.time()
    })


def clear_run_insights(run_id: str) -> None:
    """Clear insights for a run to prevent memory leaks."""
    if run_id in run_insights_cache:
        del run_insights_cache[run_id]


def is_novel_insight(insight_text: str, previous_insights: List[Dict], threshold: float = 0.8) -> bool:
    """
    Check if an insight is novel compared to previous insights using Jaccard similarity.
    Returns True if the insight is sufficiently different (novel), False if it's a duplicate.
    """
    if not previous_insights:
        return True
    
    def jaccard_similarity(text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts."""
        # Tokenize and convert to sets of words
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        # Handle empty sets
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    # Check similarity against all previous insights
    for prev_insight in previous_insights:
        similarity = jaccard_similarity(insight_text, prev_insight["text"])
        if similarity >= threshold:
            return False
    
    return True


def get_previous_insights_text(run_id: str, limit: int = 5) -> str:
    """Get previous insights as formatted text for context."""
    insights = get_run_insights(run_id)
    
    if not insights:
        return ""
    
    # Get last N insights
    recent_insights = insights[-limit:]
    
    # Format as numbered list
    formatted_insights = []
    for i, insight in enumerate(recent_insights, 1):
        step = insight.get("agent_step", "unknown")
        text = insight["text"][:120]  # Truncate to avoid overly long prompts
        formatted_insights.append(f"{i}. [{step}] {text}")
    
    return "\n".join(formatted_insights)


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
        self.min_extraction_interval = 2.0  # seconds (increased from 1.5 to reduce rate)
        self.min_chunk_size = 800  # chars (increased from 500 to wait for more content)
        
        # Deduplication cache
        self.seen_insights = LRUCache(maxsize=300)
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
                    item = await asyncio.wait_for(queue.get(), timeout=30.0)
                    event = getattr(item, "event", item)
                    
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
            
            # Get previous insights for context
            previous_insights = get_run_insights(self.job_id)
            previous_insights_text = get_previous_insights_text(self.job_id, limit=5)
            
            # Extract insights asynchronously with context
            insights = await insight_extractor.extract_insights_async(
                extraction_text, 
                agent_type, 
                max_insights=2,  # Limit to 2 insights per extraction
                previous_insights=previous_insights_text
            )
            
            # Emit non-system insights after deduplication
            for insight in insights:
                insight_text = insight["message"]
                
                # Check if this insight is novel (not a duplicate)
                if not is_novel_insight(insight_text, previous_insights):
                    print(f"🔍 Skipped duplicate insight: {insight_text[:50]}...")
                    continue
                
                insight_id = f"ins-{step}-{self.insight_counter}"
                self.insight_counter += 1
                
                # Create deduplication key for additional filtering
                dedupe_key = self._create_dedupe_key(
                    insight_text, 
                    insight["category"], 
                    step
                )
                
                # Skip if we've already seen this insight in this step (within-step dedup)
                if self.seen_insights.get(dedupe_key):
                    continue
                
                # Mark as seen
                self.seen_insights.put(dedupe_key)
                
                # Cache the insight for future deduplication checks
                cache_insight(self.job_id, insight_text, step)
                
                # Emit the insight event
                await stream_manager.emit(InsightEvent.create(
                    job_id=self.job_id,
                    insight_id=insight_id,
                    category=insight["category"],
                    importance="high",  # All real-time insights are high importance
                    message=insight_text[:80],  # Truncate to 80 chars
                    step=step
                ))
                
                print(f"🔍 Emitted insight: {insight['category']} - {insight_text[:50]}")
            
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
