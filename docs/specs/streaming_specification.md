# Real-Time Streaming Specification

## Overview

This document specifies the real-time streaming functionality for the Resume Optimizer application, which replaces mock animations with actual backend data via Server-Sent Events (SSE).

## Architecture

### Backend Streaming Infrastructure

#### Event Types
The system supports the following event types:

- **JobStatusEvent**: Job lifecycle management (started, running, completed, failed, canceled)
- **StepProgressEvent**: Per-step progress tracking with percentage and ETA
- **InsightEvent**: Real-time insights with category, importance, and message
- **MetricUpdateEvent**: Numeric metrics (scores, counts, etc.)
- **ValidationUpdateEvent**: Validation rule status updates
- **DiffChunkEvent**: Resume diff summaries
- **ErrorEvent**: Error notifications
- **HeartbeatEvent**: Keep-alive pings (15-second intervals)
- **DoneEvent**: Pipeline completion signal

#### Stream Manager
- Manages SSE connections for multiple concurrent jobs
- Maintains event history for snapshot/replay functionality
- Handles subscriber lifecycle (subscribe/unsubscribe)
- Broadcasts events to all job subscribers
- Supports late joiners via snapshot endpoint

#### API Endpoints

```
POST /api/pipeline/start
- Description: Start streaming pipeline
- Request: { resume_text, job_text?, job_url? }
- Response: { job_id, stream_url, snapshot_url }

GET /api/jobs/{job_id}/stream
- Description: SSE stream endpoint
- Response: Server-Sent Events stream

GET /api/jobs/{job_id}/snapshot
- Description: Get current job state
- Response: Current job status and event history
```

### Frontend Integration

#### TypeScript Types
```typescript
interface StreamingEvent {
  type: 'job_status' | 'step_progress' | 'insight_emitted' | 'metric_update' | 'validation_update' | 'diff_chunk' | 'error' | 'heartbeat' | 'done';
  timestamp: string;
  data: any;
}

interface StreamingState {
  insights: Insight[];
  steps: StepProgress[];
  metrics: Record<string, number>;
  currentStep: string;
  connection: ConnectionStatus;
}
```

#### React Hook (`useProcessingJob`)
- Manages SSE connection lifecycle
- Normalizes events into unified state
- Handles reconnection and error recovery
- Monitors connection health via requestAnimationFrame
- Rate-limits state updates for smooth UI (6-8 fps)

#### Component Integration
- Feature flag: `USE_STREAMING` (default: `true`)
- Syncs streaming state to existing UI components
- Converts streaming insights to legacy format for compatibility
- Calculates progress from step completion percentages
- Handles completion and error states gracefully

## Implementation Requirements

### Backend Requirements

1. **Streaming Module** (`backend/src/streaming/`)
   - `events.py`: Event type definitions and serialization
   - `manager.py`: Stream manager implementation
   - `__init__.py`: Public API exports

2. **Server Integration** (`server.py`)
   - Pipeline endpoint with event emission
   - SSE endpoint with proper headers
   - Snapshot endpoint for state recovery
   - CORS configuration for SSE

3. **Agent Integration**
   - All agents must emit events via stream_manager
   - Step progress events at key milestones
   - Insight events for user feedback
   - Error events for failure handling

### Frontend Requirements

1. **Type Definitions** (`types/streaming.ts`)
   - Complete TypeScript interfaces
   - Event union types
   - State interfaces

2. **API Service** (`services/api.ts`)
   - `startPipeline()` method
   - Error handling for SSE
   - Fallback to legacy pipeline

3. **Component Updates**
   - ProcessingScreen streaming integration
   - Real-time insight display
   - Progress bar synchronization
   - Connection status indicators

## Performance Specifications

### Rate Limiting
- Events are buffered and rate-limited to 6-8 fps
- Insights list is capped at 4 visible items
- Connection health checked via RAF, not intervals

### Memory Management
- Event history is kept in memory with TTL consideration
- SSE connections are properly cleaned up on unmount
- State updates are coalesced to prevent excessive renders

### Network Optimization
- SSE is more efficient than polling (one connection, server push)
- Events are batched when possible
- Connection auto-recovery with exponential backoff

## Security Considerations

- SSE connections are authenticated via CORS
- Job IDs are UUIDs, not guessable
- Event history is per-job, isolated
- No sensitive data in events (use references/IDs)

## Feature Flags

```typescript
// In ProcessingScreen.tsx
const USE_STREAMING = true; // Set to false to use legacy pipeline
```

## Testing Requirements

### Backend Tests
- Unit tests for event serialization
- Integration tests for stream manager
- Load testing for concurrent connections

### Frontend Tests
- Component tests for streaming integration
- Hook tests for connection management
- E2E tests for complete streaming flow

### Manual Testing
1. Start backend and frontend servers
2. Upload resume and job posting
3. Monitor console for streaming logs
4. Verify real-time insight updates
5. Test connection recovery scenarios

## Migration Path

### Phase 1: Core Infrastructure ✅
- Backend SSE infrastructure
- Stream manager implementation
- Basic event types

### Phase 2: UI Integration ✅
- Frontend streaming hook
- ProcessingScreen integration
- Real-time insights

### Phase 3: Enhanced Features 🚧
- Persistence and recovery
- Metrics visualization
- Diff display

### Phase 4: Legacy Removal 🚧
- Remove mock pipeline code
- Cleanup unused components
- Update documentation

## Error Handling

### Connection Errors
- Auto-reconnect with exponential backoff
- User notification of connection issues
- Fallback to legacy pipeline option

### Backend Errors
- Error event propagation
- Graceful degradation
- Detailed error logging

### Data Validation
- Event schema validation
- Type safety enforcement
- Malformed data handling

## Future Enhancements

1. **Persistence**: Store job_id in URL and localStorage
2. **Enhanced Insights**: Parse agent outputs for richer content
3. **Metrics Display**: Show validation scores and progress indicators
4. **Diff Visualization**: Display resume changes in real-time
5. **Validation Checklist**: Real-time rule status display
6. **Analytics**: Track event rates and user engagement

## Dependencies

### Backend
- FastAPI with SSE support
- AsyncIO for concurrent connections
- UUID generation for job IDs

### Frontend
- EventSource API for SSE
- React hooks for state management
- TypeScript for type safety

## Compatibility

- **Browsers**: All modern browsers with EventSource support
- **React**: 17+ with hooks support
- **Node.js**: 14+ for backend development
- **Python**: 3.8+ for backend runtime
