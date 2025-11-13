# Debugging SSE Streaming Issues

## Symptoms
- Frontend completes within few seconds
- Center text ("Tailoring professional summary...") changes continuously (insights working)
- Top progress bar and phase indicators NOT updating
- Ignores progression on other frontend components

## Root Cause Analysis

### Cloud Run SSE Buffering Issue
Cloud Run has a known issue with Server-Sent Events (SSE) buffering where events are **batched and sent in bursts** rather than streaming in real-time. This is caused by:

1. **nginx buffering** in Cloud Run's ingress layer
2. **Response buffering** at 4KB chunks by default
3. **Proxy buffering** between load balancer and instances

Even with `X-Accel-Buffering: no` header, Cloud Run may still buffer until:
- 4KB response size reached
- Timeout occurs
- Connection closes

### Evidence
- Insights (text changes) arrive: Insight extraction is fast (Cerebras 1000 tok/sec)
- Progress events missing: Main pipeline events (StepProgressEvent) are buffered
- Quick completion: All events arrive in a burst at the end

## Solution Options

### Option 1: Force Flush with Padding (Immediate Fix)
Add padding to each SSE message to force flush buffers > 4KB.

**Implementation:**
```python
# backend/server.py - stream_job_events()
async def event_generator():
    # Send initial heartbeat WITH PADDING
    padding = " " * 2048  # 2KB padding
    yield f"data: {json.dumps({'type': 'heartbeat', ...})}\n\n:{padding}\n\n"
    
    while True:
        event = await asyncio.wait_for(queue.get(), timeout=15.0)
        event_data = event.model_dump() if hasattr(event, 'model_dump') else event
        
        # Add padding to force immediate flush
        yield f"data: {json.dumps(event_data)}\n\n:{padding}\n\n"
        
        if event.type == "done":
            break
```

**Pros:**
- Immediate fix (no config changes)
- Forces events to flush < 1 second
- Works with existing Cloud Run setup

**Cons:**
- Wastes bandwidth (2KB per event)
- Hacky workaround

---

### Option 2: Increase Event Frequency (Recommended)
Send more frequent events to naturally exceed 4KB buffer threshold.

**Implementation:**
```python
# backend/server.py - run_agent_with_chunk_emission()
# CURRENT: Emit every 500 chars or 1.2 seconds
should_emit = (
    len(result) % 500 < len(chunk) or
    (current_time - last_emit_time) >= 1.2
)

# NEW: Emit every 100 chars or 0.3 seconds (more aggressive)
should_emit = (
    len(result) % 100 < len(chunk) or
    (current_time - last_emit_time) >= 0.3
)
```

Also add **periodic progress updates** during agent execution:
```python
# Emit intermediate progress every 5 seconds
if (current_time - last_progress_emit_time) >= 5.0:
    # Calculate progress based on token count
    progress_pct = min(95, (len(result) / 5000) * 100)  # Estimate
    stream_manager.emit_from_thread(StepProgressEvent.create(
        job_id=job_id,
        step=step_name,
        pct=progress_pct
    ))
    last_progress_emit_time = current_time
```

**Pros:**
- More natural solution
- Better real-time UX
- No wasted bandwidth

**Cons:**
- Requires code changes
- More API calls

---

### Option 3: Use Cloud Run WebSockets (Future)
Replace SSE with WebSocket connection to avoid buffering entirely.

**Not recommended for now** - requires major refactor.

---

## Recommended Immediate Fix

Combine **Option 1 (padding) + Option 2 (frequency)**:

1. Add 2KB padding to force flush
2. Increase event emission frequency (every 100 chars / 0.3s)
3. Add periodic progress updates during long agent runs

This ensures events stream in real-time even with Cloud Run buffering.

## Testing

```bash
# Monitor SSE stream in real-time
curl -N "https://your-service.run.app/api/jobs/{job_id}/stream" | \
  awk '{print strftime("%H:%M:%S"), $0; fflush()}'

# Should see events within 1-2 seconds of each other, not all at once
```

## References
- [Cloud Run SSE Buffering Issue](https://issuetracker.google.com/issues/169035839)
- [SSE Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [nginx SSE Configuration](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)
