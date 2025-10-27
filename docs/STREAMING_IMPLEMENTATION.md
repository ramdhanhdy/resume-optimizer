# Streaming Implementation Guide

## Overview

The Processing page now supports real-time streaming of pipeline progress via Server-Sent Events (SSE). This replaces the mock animations with actual data from the backend while preserving the beautiful UX.

## Architecture

### Backend (`backend/src/streaming/`)

#### Event Types (`events.py`)
- **JobStatusEvent**: Job lifecycle (started, running, completed, failed, canceled)
- **StepProgressEvent**: Per-step progress with percentage and ETA
- **InsightEvent**: Real-time insights with category, importance, and message
- **MetricUpdateEvent**: Numeric metrics (scores, counts, etc.)
- **ValidationUpdateEvent**: Validation rule status
- **DiffChunkEvent**: Resume diff summaries
- **ErrorEvent**: Error notifications
- **HeartbeatEvent**: Keep-alive pings
- **DoneEvent**: Pipeline completion signal

#### Stream Manager (`manager.py`)
- Manages SSE connections for multiple jobs
- Maintains event history for snapshot/replay
- Handles subscriber lifecycle (subscribe/unsubscribe)
- Broadcasts events to all job subscribers
- Supports late joiners via snapshot endpoint

#### API Endpoints (`server.py`)
- `POST /api/pipeline/start` - Start pipeline, returns job_id
- `GET /api/jobs/{job_id}/stream` - SSE stream endpoint
- `GET /api/jobs/{job_id}/snapshot` - Get current job state

### Frontend

#### Types (`frontend/src/types/streaming.ts`)
- TypeScript definitions for all event types
- State interfaces for UI components
- Connection state tracking

#### Hook (`frontend/src/hooks/useProcessingJob.ts`)
- Manages SSE connection lifecycle
- Normalizes events into unified state
- Handles reconnection and error recovery
- Monitors connection health
- Rate-limits state updates for smooth UI

#### Integration (`frontend/src/components/ProcessingScreen.tsx`)
- Feature flag: `USE_STREAMING` (currently `true`)
- Syncs streaming state to existing UI components
- Converts streaming insights to legacy format
- Calculates progress from step completion
- Handles completion and error states

## Current Implementation Status

### ✅ Completed
- Backend SSE infrastructure with event schema
- Stream manager with subscriber management
- Pipeline endpoint that emits real-time events
- Frontend streaming hook with state management
- ProcessingScreen integration with feature flag
- Real-time insights feed (replaces mock)
- Real-time step progress (replaces mock phases)
- Connection health monitoring
- Completion handling with application data

### 🚧 In Progress / Future Work
- **Persistence**: Store job_id in URL and localStorage for refresh support
- **Enhanced Insights**: Parse agent outputs for richer, categorized insights
- **Metrics Display**: Show validation scores and other metrics in UI
- **Diff Visualization**: Display resume changes as they're generated
- **Validation Checklist**: Real-time validation rule status
- **Error Recovery**: Retry failed steps, resync on connection loss
- **Analytics**: Track event rates, latency, and user engagement

## How to Use

### Starting the Streaming Pipeline

The ProcessingScreen automatically uses streaming when `USE_STREAMING = true`:

```typescript
// Frontend automatically calls:
const response = await apiClient.startPipeline({
  resume_text: resumeText,
  job_text: jobText,
  job_url: jobUrl,
});

// Returns: { job_id, stream_url, snapshot_url }
```

### Emitting Events from Backend

In your agent code, emit events via the stream manager:

```python
from src.streaming import stream_manager, InsightEvent, StepProgressEvent

# Emit step progress
await stream_manager.emit(
    StepProgressEvent.create(job_id, "analyzing", 50, eta_sec=30)
)

# Emit insight
await stream_manager.emit(
    InsightEvent.create(
        job_id, "ins-42", "keywords", "high",
        "Added 3 role-specific keywords", "writing"
    )
)
```

### Consuming Events in Frontend

The `useProcessingJob` hook handles everything:

```typescript
const { state, isComplete, isFailed, isConnected } = useProcessingJob(jobId);

// state.insights - Real-time insights array
// state.steps - Step progress with status
// state.metrics - Key-value metrics
// state.currentStep - Active step name
// state.connection - Connection health
```

## Feature Flag

Toggle between streaming and legacy pipeline:

```typescript
// In ProcessingScreen.tsx
const USE_STREAMING = true; // Set to false for legacy behavior
```

## UX Preservation

The implementation maintains the original beautiful UX:

- **Layout Stability**: Insights use fixed heights and smooth animations
- **Anti-Jitter**: State updates are debounced and coalesced
- **Smooth Transitions**: Phase changes use opacity/transform animations
- **Progress Continuity**: Progress bar smoothly reflects step completion
- **Visual Hierarchy**: Important insights are prioritized

## Testing

### Backend
```bash
cd backend
python -m pytest tests/test_streaming.py  # TODO: Create tests
```

### Frontend
```bash
cd frontend
npm run dev

# Open browser console to see streaming logs:
# 🔌 Connecting to SSE stream
# ✅ SSE connection opened
# 📡 Received event: { type: 'insight_emitted', ... }
```

### Manual Testing
1. Start backend: `cd backend && python server.py`
2. Start frontend: `cd frontend && npm run dev`
3. Upload resume and job posting
4. Watch console for streaming events
5. Verify insights appear in real-time
6. Check progress bar updates smoothly

## Troubleshooting

### No events received
- Check backend logs for stream manager errors
- Verify CORS settings allow SSE
- Check browser console for connection errors
- Ensure job_id is valid

### Connection drops
- SSE auto-reconnects by default
- Check firewall/proxy settings
- Verify heartbeat events are sent every 15s

### Insights not showing
- Check event payload format matches schema
- Verify insight conversion in ProcessingScreen
- Check browser console for type errors

## Next Steps

1. **Add URL persistence**: Store job_id in URL params
2. **Implement localStorage cache**: Fast warm re-render on refresh
3. **Enhanced error UX**: Per-step retry buttons, detailed error messages
4. **Metrics visualization**: Show scores, counts, and progress indicators
5. **Diff display**: Expandable cards showing resume changes
6. **Validation checklist**: Real-time rule status with pass/warn/fail indicators

## Migration Path

To fully migrate away from mocks:

1. ✅ Phase 1: Core streaming infrastructure (DONE)
2. ✅ Phase 2: Insights and step progress (DONE)
3. 🚧 Phase 3: Metrics and validation display
4. 🚧 Phase 4: Diff visualization
5. 🚧 Phase 5: Persistence and recovery
6. 🚧 Phase 6: Remove legacy pipeline code

## Performance Considerations

- Events are buffered and rate-limited to 6-8 fps
- Insights list is capped at 4 visible items
- Connection health checked via RAF, not intervals
- Event history is kept in memory (consider TTL for cleanup)
- SSE is more efficient than polling (one connection, server push)

## Security Notes

- SSE connections are authenticated via CORS
- job_id is a UUID, not guessable
- Event history is per-job, isolated
- No sensitive data in events (use references/IDs)
