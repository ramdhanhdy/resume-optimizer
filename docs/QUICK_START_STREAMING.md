# Quick Start: Streaming Implementation

## What Changed?

The Processing page now uses **real-time Server-Sent Events (SSE)** instead of mock animations. The insights, step progress, and phase updates you see are now **actual data from the backend pipeline**.

## Key Files

### Backend
- `backend/src/streaming/` - New streaming infrastructure
  - `events.py` - Event type definitions
  - `manager.py` - Stream manager for SSE connections
  - `__init__.py` - Public API
- `backend/server.py` - Added:
  - `POST /api/pipeline/start` - Start streaming pipeline
  - `GET /api/jobs/{job_id}/stream` - SSE endpoint
  - `GET /api/jobs/{job_id}/snapshot` - State snapshot
  - `run_pipeline_with_streaming()` - Pipeline with events

### Frontend
- `frontend/src/types/streaming.ts` - TypeScript event types
- `frontend/src/hooks/useProcessingJob.ts` - SSE state management hook
- `frontend/src/services/api.ts` - Added `startPipeline()` method
- `frontend/src/components/ProcessingScreen.tsx` - Integrated streaming
- `frontend/src/vite-env.d.ts` - Vite environment types

## How to Test

### 1. Start the backend
```bash
cd backend
python server.py
```

### 2. Start the frontend
```bash
cd frontend
npm run dev
```

### 3. Use the app
1. Upload a resume
2. Paste a job posting
3. Click "Optimize Resume"
4. **Watch the browser console** for streaming logs:
   - `🔌 Connecting to SSE stream`
   - `✅ SSE connection opened`
   - `📡 Starting streaming pipeline...`
   - Events will stream in real-time

### 4. Observe the UI
- **Phase text** (top-left) updates as steps progress
- **Insights cards** (right side) populate with real messages
- **Progress bar** (bottom) reflects actual completion
- **No more mock timers!**

## Feature Flag

In `ProcessingScreen.tsx`, line 19:

```typescript
const USE_STREAMING = true; // Set to false to use legacy pipeline
```

## What's Real vs. Mock?

### ✅ Now Real (from backend events)
- Phase/step names ("Analyzing job...", "Planning optimizations...", etc.)
- Insights messages and categories
- Progress percentage
- Completion detection

### 🚧 Still Mock (to be implemented)
- Activity text cycling (the large center text)
- Detailed metrics display
- Validation checklist
- Resume diffs

## Adding More Insights

In your backend agent code:

```python
from src.streaming import stream_manager, InsightEvent

# Emit an insight
await stream_manager.emit(
    InsightEvent.create(
        job_id=job_id,
        insight_id="ins-unique-id",
        category="keywords",  # or "analysis", "strategy", etc.
        importance="high",    # "low", "medium", "high"
        message="Added 5 technical keywords matching job requirements",
        step="writing"        # optional: which step this belongs to
    )
)
```

## Common Issues

### "Connection lost" in UI
- Check backend is running on port 8000
- Verify CORS settings in `server.py`
- Check browser console for errors

### No insights appearing
- Verify `USE_STREAMING = true` in ProcessingScreen
- Check backend logs for event emissions
- Ensure `job_id` is being set correctly

### Progress stuck at 0%
- Verify `StepProgressEvent` emissions in backend
- Check step names match: `analyzing`, `planning`, `writing`, `validating`, `polishing`

## Next Steps

1. **Test the streaming pipeline** end-to-end
2. **Add more insights** in agent code for richer feedback
3. **Implement metrics display** (validation scores, etc.)
4. **Add URL persistence** for job_id (refresh support)
5. **Create diff visualization** for resume changes

## Rollback

To revert to the old mock-based pipeline:

```typescript
// In ProcessingScreen.tsx
const USE_STREAMING = false;
```

The old pipeline code is still intact and will work as before.
