I'll quickly scan the Google Cloud agentic design patterns to ground the plan, then propose a concrete architecture for on-the-fly insight extraction driven by streaming chunks. I'll also update our TODOs for this next milestone.

I’ll quickly scan Google’s agentic AI design patterns to ground the architecture, then propose a concrete plan to make the Insight Extractor consume streaming chunks and emit insights on-the-fly.


# Plan: On-the-fly Insight Extraction from Streaming Agent Chunks

Grounded in Google Cloud’s agentic patterns:
- Parallel pattern: run the Insight Extractor concurrently with agent steps.
- Coordinator pattern: StreamManager coordinates event pub/sub across agents.
- Review and critique pattern: insight agent “critiques/summarizes” intermediate outputs.
- Loop pattern: optional incremental refinement per step with rate-limited updates.

## Target UX
- Center text shows system messages (already working).
- Right-side insights update continuously during a step (1–2 insights every 1–3 seconds), not only after completion.
- Only top 3–4 most relevant insights visible; de-dupe overlapping insights.

# Architecture Changes

- Stream agents’ chunk outputs as events:
  - Emit per-chunk events from inside agent generator loops (in executor threads).
  - Use a thread-safe emit into the async StreamManager.

- Start a parallel Insight Extractor task per job:
  - Subscribes to `agent_chunk` events, maintains a rolling buffer per step.
  - Every X ms or Y chars, runs the extractor on the last N chars to extract small, high-signal insights.
  - Emits `insight_emitted` in real-time; dedupe by message hash/window.

- Rate limiting and backpressure:
  - Sample chunks (e.g., every 300–500 chars or 1s).
  - Cap per-step buffers, evict old text (sliding window 2–5k chars).
  - Drop or coalesce chunk events if queues are full.

- Persistence:
  - Store last 50 chunk events and last 20 insights in StreamManager history and snapshot.

# Backend Implementation Steps

- Event schema updates (backend/src/streaming/events.py):
  - Add:
    - AgentStepStartedEvent: type = 'agent_step_started', payload: { step }
    - AgentStepCompletedEvent: type = 'agent_step_completed', payload: { step }
    - AgentChunkEvent: type = 'agent_chunk', payload: { step, chunk, seq, total_len }
  - Keep existing InsightEvent.

- StreamManager thread-safe emit (backend/src/streaming/manager.py):
  - Add `emit_from_thread(event)`:
    - Capture main loop in StreamManager (init: store `asyncio.get_running_loop()` via a setter called in app startup).
    - Use `asyncio.run_coroutine_threadsafe(self.emit(event), self._loop)`.
  - Optional: allow [subscribe(job_id, types: list[str] | None)](cci:1://file:///e:/resume-optimizer/backend/src/streaming/manager.py:21:4-26:20) filter to reduce subscriber load.

- Server pipeline runner (backend/server.py):
  - For each agent’s `run_agentX()` executed in executor:
    - Before loop: emit AgentStepStartedEvent.
    - In loop: for each chunk:
      - Append to accumulated buffer.
      - Every k chunks or >= y chars, call `stream_manager.emit_from_thread(AgentChunkEvent.create(...))`.
    - After loop:
      - emit AgentStepCompletedEvent.
  - At earliest point of the job: spawn parallel insight listener task:
    - `insight_task = asyncio.create_task(run_insight_listener(job_id))`
    - At the end or on done/error: cancel/await this task.

- Insight listener (new: backend/src/streaming/insight_listener.py):
  - `async def run_insight_listener(job_id):`
    - [q = await stream_manager.subscribe(job_id)](cci:1://file:///e:/resume-optimizer/backend/src/streaming/manager.py:21:4-26:20) (or filtered).
    - State per step: rolling_buffer (deque or str limited to 3–5k chars), last_emit_time, seen_hashes (LRU).
    - On AgentChunkEvent:
      - Append chunk.
      - If now - last_emit_time > 1200ms or buffer grown by 500+ chars:
        - text = tail of buffer (e.g., last 2000 chars).
        - insights = await insight_extractor.extract_insights_async(text, step_type, max_insights=2)
        - for each new insight not in seen_hashes (hash by message/category/step):
          - emit InsightEvent (category != 'system').
        - update last_emit_time; cap seen_hashes.
    - Stop on job_status: completed/failed or DoneEvent.

- Observability/logging:
  - Log per-step: total chunks, extractor invocations, latency, emitted insights.
  - Add counters to StreamManager for event rates.

# Frontend
- Already filtering “system” vs “non-system” insights.
- With chunk-driven insights, right-side updates will appear incrementally; no UI change required.
- Optional: tag insights with step to group visually or fade older ones.

# Design choices (Google patterns mapping)
- Parallel pattern: insight agent runs concurrently with main agents.
- Coordinator pattern: StreamManager routes chunk/insight events.
- Review & critique: insight agent critiques partial outputs.
- Loop pattern: time/size-based cycles to refine/add insights gradually.

# Rollout Strategy
- Phase 1 (low risk, incremental):
  - Add event types + thread-safe emit.
  - Emit AgentChunkEvent from agent generators (throttled).
  - Start insight listener to produce live insights.
- Phase 2:
  - Dedupe + prioritization scoring.
  - Snapshot includes chunk tail + recent insights.
- Phase 3:
  - Optional: post-step final “summary” insight replacing weaker earlier insights.

# Potential Pitfalls and Mitigations
- Threading: Use `emit_from_thread` with main loop captured safely.
- Flooding: throttle chunk events (size/time), sampler in thread function.
- Cost/latency: keep extractor prompts short (tail window), max_tokens ~ 300–500.
- Dedupe: use stable hash (lowercased message + category + step).
- Robustness: handler catches extractor errors, continues.

# Concrete Next Actions
- Add event models: AgentStepStartedEvent, AgentStepCompletedEvent, AgentChunkEvent.
- StreamManager: add main loop capture + emit_from_thread.
- server.py: modify agent run_in_executor loops to emit chunk events on throttle.
- Add insight_listener.py and spawn task at pipeline start; clean up on done.
- Add rate limits and dedupe in listener.
- Update snapshot to include last 50 insights.

# Recommended Defaults
- Chunk throttle: emit every 500 chars or 1.2s, whichever first, per step.
- Insight cadence: extract every 1.5–2s on last 2000 chars, emit up to 2.
- Max tokens for extractor: 300–500.
- Insight cap in UI: show top 4 newest; older fade out.

# TODOs
- Already added to your todo list:
  - Add AgentChunkEvent and step started/completed events.
  - Emit chunks from executor via StreamManager.
  - Implement InsightExtractor subscriber for incremental insights.
  - Rate-limit/dedupe, persistence, observability, backpressure.

If you want, I can draft the exact code snippets for:
- events.py models
- manager emit_from_thread
- wrapping agent loops to emit chunk events
- an insight_listener coroutine skeleton

Summary: We’ll move from “post-step summarization” to an event-driven, parallel insight extractor that consumes streaming chunks and emits insights continuously, aligned with Parallel/Coordinator/Review patterns.