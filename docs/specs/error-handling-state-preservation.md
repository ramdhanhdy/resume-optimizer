# Error Handling and State Preservation System

**Version:** 1.0
**Date:** 2025-10-31
**Status:** Draft
**Authors:** System Architecture Team

---

## Executive Summary

This specification defines a comprehensive error handling and state preservation system for the AI Resume Optimizer application. The system ensures zero data loss during pipeline failures by automatically capturing and persisting all user inputs, uploaded files, and processing state. Upon failure, users are seamlessly redirected to the input screen with all data preserved, clear error messaging, and options for automatic retry or manual recovery.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Requirements](#2-requirements)
3. [System Architecture](#3-system-architecture)
4. [Error Detection Strategy](#4-error-detection-strategy)
5. [State Preservation Mechanisms](#5-state-preservation-mechanisms)
6. [Recovery Flows](#6-recovery-flows)
7. [Implementation Details](#7-implementation-details)
8. [Security Considerations](#8-security-considerations)
9. [Performance Considerations](#9-performance-considerations)
10. [Testing Strategy](#10-testing-strategy)
11. [Rollout Plan](#11-rollout-plan)

---

## 1. Problem Statement

### 1.1 Current State

The AI Resume Optimizer processes resumes through a 5-agent pipeline:
1. JobAnalyzerAgent
2. ResumeOptimizerAgent
3. OptimizerImplementerAgent
4. ValidatorAgent
5. PolishAgent

**Current Issues:**
- Pipeline failures result in complete loss of user input data
- Uploaded resume files are lost on error
- No automatic retry mechanism exists
- Users must re-upload and re-enter all information
- No error context preservation for debugging
- Poor user experience during failure scenarios

### 1.2 Impact

- **User Frustration**: Loss of time-sensitive job application data
- **Data Loss**: Resume files (potentially large) must be re-uploaded
- **Operational Overhead**: Support tickets for recurring failures
- **Debugging Difficulty**: No failure context for troubleshooting
- **Conversion Loss**: Users abandon the application after failures

### 1.3 Goals

1. **Zero Data Loss**: Preserve 100% of user input during failures
2. **Seamless Recovery**: Auto-restore state on return to input screen
3. **Failure Transparency**: Clear error messages with actionable next steps
4. **Intelligent Retry**: Automatic retry for transient failures
5. **Debugging Support**: Comprehensive failure logging and context
6. **Cross-Session Persistence**: State survives browser refresh/close

---

## 2. Requirements

### 2.1 Functional Requirements

#### FR-1: State Capture
- **FR-1.1**: Capture all form inputs (job posting text/URL, user preferences)
- **FR-1.2**: Capture uploaded resume file (PDF, DOCX, images)
- **FR-1.3**: Capture processing progress (which agents completed)
- **FR-1.4**: Capture error context (error type, message, stack trace)
- **FR-1.5**: Capture timestamp and session metadata

#### FR-2: Error Detection
- **FR-2.1**: Detect network failures (timeout, connection loss)
- **FR-2.2**: Detect agent processing failures (LLM errors, validation failures)
- **FR-2.3**: Detect system errors (memory, file system, database)
- **FR-2.4**: Detect timeout scenarios (long-running agents)
- **FR-2.5**: Detect rate limiting from LLM providers

#### FR-3: State Persistence
- **FR-3.1**: Store state in browser LocalStorage (< 5MB data)
- **FR-3.2**: Store large files in IndexedDB (resume files)
- **FR-3.3**: Store server-side state in database for recovery
- **FR-3.4**: Maintain state consistency across storage layers
- **FR-3.5**: Auto-expire stale sessions after 7 days

#### FR-4: Recovery UX
- **FR-4.1**: Redirect to input screen on failure
- **FR-4.2**: Display error banner with failure details
- **FR-4.3**: Auto-populate all form fields with preserved data
- **FR-4.4**: Show uploaded file preview/name
- **FR-4.5**: Provide "Retry" button for automatic recovery
- **FR-4.6**: Provide "Start Fresh" button to clear state
- **FR-4.7**: Show recovery timestamp ("Data from 5 minutes ago")

#### FR-5: Retry Mechanism
- **FR-5.1**: Automatic retry with exponential backoff for network errors
- **FR-5.2**: Resume from last successful agent (partial pipeline retry)
- **FR-5.3**: Max 3 automatic retries, then require manual intervention
- **FR-5.4**: Smart retry: Skip completed agents, resume from failure point
- **FR-5.5**: Retry with fallback model if primary LLM fails

#### FR-6: Error Messaging
- **FR-6.1**: User-friendly error descriptions (not stack traces)
- **FR-6.2**: Actionable next steps ("Try again" vs "Contact support")
- **FR-6.3**: Error categorization (temporary vs permanent)
- **FR-6.4**: Estimated recovery time for transient issues
- **FR-6.5**: Support reference ID for troubleshooting

### 2.2 Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: State capture must complete within 500ms
- **NFR-1.2**: State restoration must complete within 1 second
- **NFR-1.3**: File storage/retrieval must handle up to 10MB files
- **NFR-1.4**: No noticeable UI latency during state operations

#### NFR-2: Reliability
- **NFR-2.1**: 99.9% success rate for state capture
- **NFR-2.2**: State must survive browser refresh/close
- **NFR-2.3**: Graceful degradation if storage is unavailable
- **NFR-2.4**: No data corruption during storage operations

#### NFR-3: Security
- **NFR-3.1**: Resume files encrypted at rest in IndexedDB
- **NFR-3.2**: State data sanitized to prevent XSS
- **NFR-3.3**: Session tokens expire after 7 days
- **NFR-3.4**: No PII exposed in error logs
- **NFR-3.5**: Secure cleanup of expired sessions

#### NFR-4: Compatibility
- **NFR-4.1**: Support Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **NFR-4.2**: Handle LocalStorage quota exceeded scenarios
- **NFR-4.3**: Fallback to SessionStorage if LocalStorage unavailable
- **NFR-4.4**: Work offline (if failure occurs during network loss)

#### NFR-5: Maintainability
- **NFR-5.1**: Centralized error handling service
- **NFR-5.2**: Comprehensive logging for debugging
- **NFR-5.3**: Metrics dashboard for failure tracking
- **NFR-5.4**: Error patterns analysis for proactive fixes

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ InputScreen  │──▶│ Processing   │──▶│ RevealScreen │    │
│  │              │   │ Screen       │   │              │    │
│  └──────┬───────┘   └──────┬───────┘   └──────────────┘    │
│         │                  │                                 │
│         │                  │                                 │
│  ┌──────▼──────────────────▼─────────────────────────────┐  │
│  │         Error Handler & State Manager                  │  │
│  │                                                         │  │
│  │  • Error Detection          • State Persistence       │  │
│  │  • State Capture            • Recovery Logic          │  │
│  │  • Retry Coordination       • UI State Management     │  │
│  └──────┬─────────────────────┬────────────┬─────────────┘  │
│         │                     │            │                 │
│  ┌──────▼──────┐       ┌──────▼──────┐    │                 │
│  │ LocalStorage│       │  IndexedDB  │    │                 │
│  │             │       │             │    │                 │
│  │ • Form Data │       │ • Files     │    │                 │
│  │ • Metadata  │       │ • Blobs     │    │                 │
│  └─────────────┘       └─────────────┘    │                 │
│                                            │                 │
└────────────────────────────────────────────┼─────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Network       │
                                    │   (SSE/HTTP)    │
                                    └────────┬────────┘
┌────────────────────────────────────────────┼─────────────────┐
│                       Backend Layer         │                 │
├─────────────────────────────────────────────┼─────────────────┤
│                                            │                 │
│  ┌────────────────────────────────────────▼──────────────┐  │
│  │          Error Interceptor Middleware                  │  │
│  │                                                         │  │
│  │  • Pipeline Monitoring      • Failure Detection       │  │
│  │  • State Checkpoint         • Error Classification    │  │
│  └────────┬──────────────────────────────┬─────────────────┘  │
│           │                              │                 │
│  ┌────────▼──────────┐        ┌──────────▼──────────┐    │
│  │ Agent Pipeline    │        │  Recovery Service   │    │
│  │                   │        │                     │    │
│  │ • Agent 1-5       │◀───────│ • Retry Logic       │    │
│  │ • Streaming       │        │ • State Restore     │    │
│  │ • Checkpointing   │        │ • Fallback Models   │    │
│  └───────────────────┘        └─────────────────────┘    │
│           │                                               │
│  ┌────────▼───────────────────────────────────────────┐  │
│  │              Database Layer                         │  │
│  │                                                     │  │
│  │  • applications (with recovery metadata)           │  │
│  │  • agent_outputs (checkpointed)                    │  │
│  │  • error_logs (detailed failure context)           │  │
│  │  • recovery_sessions (state snapshots)             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Component Descriptions

#### 3.2.1 Frontend Components

**ErrorBoundary (React Component)**
- Wraps application root to catch React errors
- Triggers state preservation on unhandled errors
- Shows user-friendly error UI
- Provides recovery options

**StateManager Service**
- Singleton service managing application state
- Orchestrates state capture/restoration
- Manages storage layer interactions
- Handles state versioning and migration

**StorageAdapter Interface**
- Abstract interface for storage operations
- Implementations: LocalStorageAdapter, IndexedDBAdapter
- Handles quota management and fallbacks
- Provides encryption/decryption for sensitive data

**ErrorHandler Service**
- Centralizes error detection and classification
- Emits error events to state manager
- Maps errors to user-friendly messages
- Coordinates retry logic

**RetryCoordinator**
- Implements exponential backoff
- Tracks retry attempts and success rates
- Decides on automatic vs manual retry
- Manages fallback strategies

#### 3.2.2 Backend Components

**ErrorInterceptor Middleware**
- FastAPI middleware intercepting all requests
- Detects pipeline failures in real-time
- Triggers state checkpointing
- Enriches error responses with recovery metadata

**PipelineMonitor**
- Monitors agent execution progress
- Creates checkpoints after each agent
- Detects timeouts and stalls
- Emits progress events via SSE

**RecoveryService**
- Manages pipeline resume logic
- Loads checkpointed state from database
- Skips completed agents on retry
- Handles model fallback strategies

**ErrorLogger**
- Structured logging of all errors
- Stores error context in database
- Generates support reference IDs
- Provides analytics on error patterns

### 3.3 Data Flow

#### 3.3.1 Normal Processing Flow

```
1. User enters data in InputScreen
2. User uploads resume file
3. Submit triggers optimization request
4. Frontend transitions to ProcessingScreen
5. SSE connection established for progress
6. Backend executes agent pipeline (1→2→3→4→5)
7. Each agent success creates checkpoint in DB
8. Final result stored in applications table
9. Frontend transitions to RevealScreen
10. User views optimized resume
```

#### 3.3.2 Failure Detection Flow

```
1. Error occurs during pipeline execution
   - Network timeout (frontend)
   - Agent processing error (backend)
   - LLM API failure (backend)
   - System resource error (backend)

2. ErrorInterceptor catches exception
   - Determines error category (transient/permanent)
   - Logs detailed context to error_logs table
   - Generates support reference ID
   - Retrieves last successful checkpoint

3. Backend sends error event via SSE
   - Error type and message
   - Last successful agent
   - Recovery metadata (session ID, checkpoint ID)
   - Retry recommendation

4. Frontend ErrorHandler receives event
   - Triggers StateManager.captureState()
   - Shows error notification
   - Determines if automatic retry appropriate

5. StateManager captures current state
   - Extracts form data from input state
   - Retrieves file from IndexedDB
   - Stores recovery session in LocalStorage
   - Associates with backend session ID

6. User redirected to InputScreen
   - Error banner displayed at top
   - All fields auto-populated from preserved state
   - File preview shown
   - "Retry" and "Start Fresh" buttons visible
```

#### 3.3.3 Recovery Flow (Automatic Retry)

```
1. Frontend determines automatic retry appropriate
   - Error is transient (network, timeout)
   - Retry count < 3
   - Less than 2 minutes since last attempt

2. RetryCoordinator initiates retry
   - Waits exponential backoff (2^n seconds)
   - Sends retry request with session ID
   - Includes checkpoint ID for resume

3. Backend RecoveryService receives retry
   - Loads session from recovery_sessions table
   - Retrieves checkpointed agent outputs
   - Identifies last successful agent
   - Resumes pipeline from next agent

4. Pipeline executes remaining agents
   - Agent 1-N: Skipped (load from checkpoint)
   - Agent N+1: Resume execution
   - Agent N+2 to 5: Continue normally

5. Success or failure
   - Success: User transitions to RevealScreen
   - Failure: Repeat detection flow (max 3 times)
```

#### 3.3.4 Recovery Flow (Manual Retry)

```
1. User clicks "Retry" button on InputScreen

2. Frontend StateManager.restoreAndRetry()
   - Loads state from LocalStorage
   - Restores form fields
   - Retrieves file from IndexedDB
   - Sends new optimization request with recovery flag

3. Backend checks for existing session
   - If found: Resume from checkpoint
   - If not found: Start fresh pipeline
   - Preserves original timestamp in metadata

4. Pipeline executes
   - May use fallback model if primary failed
   - User sees progress in ProcessingScreen
   - All checkpoints created normally

5. Completion
   - State cleanup on success
   - Error banner persists on failure with new context
```

---

## 4. Error Detection Strategy

### 4.1 Error Categories

#### Category 1: Transient Errors (Auto-Retry)
- **Network Timeouts**: Request > 2 minutes
- **Connection Loss**: SSE disconnection
- **Rate Limiting**: 429 status from LLM provider
- **Temporary Unavailability**: 503 from backend
- **Memory Pressure**: Temporary resource constraints

**Characteristics:**
- Likely to succeed on retry
- No user intervention needed
- Auto-retry with exponential backoff
- Max 3 attempts before manual intervention

#### Category 2: Recoverable Errors (Manual Retry)
- **LLM API Errors**: Model unavailable, context length exceeded
- **Agent Processing Errors**: Validation failure, parsing errors
- **File Processing Errors**: Corrupt file, unsupported format
- **Database Errors**: Connection pool exhausted

**Characteristics:**
- May require model fallback or user action
- Manual retry recommended
- State preserved for user decision
- Fallback strategies available

#### Category 3: Permanent Errors (No Retry)
- **Authentication Errors**: Invalid API key
- **Authorization Errors**: Insufficient permissions
- **Validation Errors**: Invalid input format
- **System Configuration Errors**: Missing environment variables

**Characteristics:**
- Will not succeed on retry without changes
- Require user or admin intervention
- Clear error messages with next steps
- State preserved but retry disabled

### 4.2 Detection Mechanisms

#### Frontend Detection

**Network Errors**
```typescript
// Axios interceptor
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.code === 'ECONNABORTED') {
      // Timeout detected
      await errorHandler.handle({
        type: 'NETWORK_TIMEOUT',
        category: 'TRANSIENT',
        originalError: error
      });
    }

    if (!error.response && error.request) {
      // Network failure (no response)
      await errorHandler.handle({
        type: 'NETWORK_FAILURE',
        category: 'TRANSIENT',
        originalError: error
      });
    }

    throw error;
  }
);
```

**SSE Connection Errors**
```typescript
// EventSource error handling
eventSource.onerror = (event) => {
  if (eventSource.readyState === EventSource.CLOSED) {
    errorHandler.handle({
      type: 'SSE_CONNECTION_LOST',
      category: 'TRANSIENT',
      context: { lastEventTime: lastMessageTime }
    });
  }
};
```

**React Error Boundary**
```typescript
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    errorHandler.handle({
      type: 'REACT_ERROR',
      category: 'RECOVERABLE',
      error,
      errorInfo,
      componentStack: errorInfo.componentStack
    });

    stateManager.captureState({
      reason: 'REACT_ERROR',
      timestamp: Date.now()
    });
  }
}
```

#### Backend Detection

**FastAPI Exception Handlers**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    error_id = generate_error_id()
    category = classify_error(exc)

    # Log detailed error
    await error_logger.log_error(
        error_id=error_id,
        exception=exc,
        request=request,
        category=category,
        traceback=traceback.format_exc()
    )

    # Save checkpoint if session exists
    session_id = request.headers.get('X-Session-ID')
    if session_id:
        await recovery_service.create_checkpoint(
            session_id=session_id,
            error_id=error_id
        )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_id": error_id,
            "category": category,
            "message": get_user_message(category),
            "retryable": category in ['TRANSIENT', 'RECOVERABLE'],
            "recovery_metadata": {
                "session_id": session_id,
                "checkpoint_available": session_id is not None
            }
        }
    )
```

**Agent Pipeline Monitoring**
```python
async def execute_agent_pipeline(session_id: str, ...):
    """Execute agent pipeline with checkpointing"""
    try:
        for i, agent in enumerate(agents):
            # Check for timeout
            with timeout(seconds=300):  # 5 minute per agent
                result = await agent.run(...)

            # Checkpoint after each success
            await recovery_service.save_checkpoint(
                session_id=session_id,
                agent_index=i,
                agent_name=agent.name,
                result=result
            )

    except TimeoutError:
        raise AgentTimeoutError(
            agent=agent.name,
            session_id=session_id,
            category='TRANSIENT'
        )
    except LLMError as e:
        # Classify LLM-specific errors
        category = 'TRANSIENT' if e.status_code == 429 else 'RECOVERABLE'
        raise PipelineError(
            agent=agent.name,
            session_id=session_id,
            category=category,
            original_error=e
        )
```

### 4.3 Error Classification Rules

```python
def classify_error(exc: Exception) -> ErrorCategory:
    """Classify exception into error category"""

    # Transient errors
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return 'TRANSIENT'

    if isinstance(exc, httpx.TimeoutException):
        return 'TRANSIENT'

    if isinstance(exc, httpx.ConnectError):
        return 'TRANSIENT'

    if hasattr(exc, 'status_code') and exc.status_code in [429, 503]:
        return 'TRANSIENT'

    # Recoverable errors
    if isinstance(exc, (AgentProcessingError, ValidationError)):
        return 'RECOVERABLE'

    if isinstance(exc, LLMError):
        if exc.status_code in [500, 502, 504]:
            return 'RECOVERABLE'
        if 'context_length_exceeded' in str(exc):
            return 'RECOVERABLE'

    # Permanent errors
    if isinstance(exc, (AuthenticationError, AuthorizationError)):
        return 'PERMANENT'

    if isinstance(exc, ConfigurationError):
        return 'PERMANENT'

    # Default to recoverable for safety
    return 'RECOVERABLE'
```

---

## 5. State Preservation Mechanisms

### 5.1 State Schema

#### Frontend State (LocalStorage)

```typescript
interface RecoverySession {
  // Metadata
  sessionId: string;              // UUID v4
  version: string;                // Schema version (e.g., "1.0")
  createdAt: number;              // Unix timestamp
  expiresAt: number;              // Unix timestamp (createdAt + 7 days)

  // User Input State
  formData: {
    jobPosting: string;           // Job posting text or URL
    isJobUrl: boolean;            // True if URL, false if text
    additionalNotes?: string;     // Optional user notes
  };

  // File State
  fileMetadata: {
    fileName: string;
    fileSize: number;
    fileType: string;             // MIME type
    indexedDBKey: string;         // Reference to IndexedDB blob
    uploadedAt: number;           // Unix timestamp
    fileHash: string;             // SHA-256 hash for integrity
  } | null;

  // Processing State
  processingState: {
    status: 'pending' | 'processing' | 'failed';
    currentAgent: number | null;  // 0-4 for agent index
    completedAgents: number[];    // Array of completed agent indices
    lastCheckpointId: string | null;  // Backend checkpoint reference
  };

  // Error Context
  errorContext: {
    errorId: string;              // Backend error reference ID
    errorType: string;            // Error classification
    errorMessage: string;         // User-friendly message
    category: 'TRANSIENT' | 'RECOVERABLE' | 'PERMANENT';
    occurredAt: number;           // Unix timestamp
    retryCount: number;           // Number of retry attempts
    lastRetryAt: number | null;   // Last retry timestamp
  } | null;

  // Recovery Metadata
  recovery: {
    canAutoRetry: boolean;
    canManualRetry: boolean;
    suggestedAction: string;      // User guidance
    supportReferenceId: string;   // For support tickets
  };
}
```

**LocalStorage Key:** `resume_optimizer_recovery_${sessionId}`

#### Backend State (Database)

**New Table: `recovery_sessions`**

```sql
CREATE TABLE recovery_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    application_id INTEGER,  -- FK to applications table (nullable)

    -- User input state (JSON)
    form_data TEXT NOT NULL,  -- JSON: job posting, notes

    -- File metadata (JSON)
    file_metadata TEXT,  -- JSON: file info, storage location

    -- Processing state
    status TEXT NOT NULL,  -- pending, processing, failed, recovered
    current_agent INTEGER,  -- 0-4
    completed_agents TEXT,  -- JSON array: [0, 1, 2]

    -- Error context
    error_id TEXT,
    error_type TEXT,
    error_category TEXT,  -- TRANSIENT, RECOVERABLE, PERMANENT
    error_message TEXT,
    error_stacktrace TEXT,

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- created_at + 7 days

    -- Foreign key
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE INDEX idx_recovery_session_id ON recovery_sessions(session_id);
CREATE INDEX idx_recovery_expires ON recovery_sessions(expires_at);
```

**New Table: `agent_checkpoints`**

```sql
CREATE TABLE agent_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_index INTEGER NOT NULL,  -- 0-4
    agent_name TEXT NOT NULL,  -- JobAnalyzer, ResumeOptimizer, etc.

    -- Agent output (JSON)
    agent_output TEXT NOT NULL,  -- Full agent result

    -- Metadata
    execution_time_ms INTEGER,
    model_used TEXT,
    tokens_used INTEGER,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES recovery_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_checkpoint_session ON agent_checkpoints(session_id);
CREATE INDEX idx_checkpoint_agent ON agent_checkpoints(session_id, agent_index);
```

**New Table: `error_logs`**

```sql
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_id TEXT UNIQUE NOT NULL,
    session_id TEXT,

    -- Error details
    error_type TEXT NOT NULL,
    error_category TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_stacktrace TEXT,

    -- Request context
    request_path TEXT,
    request_method TEXT,
    user_agent TEXT,
    ip_address TEXT,

    -- Additional context (JSON)
    additional_context TEXT,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES recovery_sessions(session_id) ON DELETE SET NULL
);

CREATE INDEX idx_error_id ON error_logs(error_id);
CREATE INDEX idx_error_session ON error_logs(session_id);
CREATE INDEX idx_error_created ON error_logs(created_at);
```

### 5.2 Storage Strategies

#### 5.2.1 LocalStorage Strategy

**Advantages:**
- Synchronous API (simple to use)
- Persists across browser sessions
- No quota prompts for small data

**Limitations:**
- 5-10MB limit (browser-dependent)
- Synchronous operations (can block UI)
- String-only storage

**Usage:**
- Form input data (< 100KB)
- Session metadata
- Error context
- Recovery flags

**Implementation:**
```typescript
class LocalStorageAdapter {
  private readonly prefix = 'resume_optimizer_';

  saveSession(session: RecoverySession): void {
    try {
      const key = `${this.prefix}recovery_${session.sessionId}`;
      const serialized = JSON.stringify(session);

      // Check size
      if (serialized.length > 1024 * 1024) {  // 1MB limit for safety
        throw new Error('Session data too large for LocalStorage');
      }

      localStorage.setItem(key, serialized);
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        // Cleanup old sessions
        this.cleanupOldSessions();
        // Retry
        localStorage.setItem(key, serialized);
      } else {
        throw e;
      }
    }
  }

  loadSession(sessionId: string): RecoverySession | null {
    const key = `${this.prefix}recovery_${sessionId}`;
    const data = localStorage.getItem(key);

    if (!data) return null;

    const session = JSON.parse(data) as RecoverySession;

    // Check expiration
    if (Date.now() > session.expiresAt) {
      this.deleteSession(sessionId);
      return null;
    }

    return session;
  }

  cleanupOldSessions(): void {
    const now = Date.now();

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(`${this.prefix}recovery_`)) continue;

      const data = localStorage.getItem(key);
      if (!data) continue;

      const session = JSON.parse(data) as RecoverySession;
      if (now > session.expiresAt) {
        localStorage.removeItem(key);
      }
    }
  }
}
```

#### 5.2.2 IndexedDB Strategy

**Advantages:**
- Large storage capacity (50MB - 1GB+)
- Asynchronous API (non-blocking)
- Can store Blobs/Files directly

**Limitations:**
- Asynchronous (more complex)
- More verbose API
- Browser compatibility considerations

**Usage:**
- Resume files (PDF, DOCX, images)
- Large job posting content
- Cached agent outputs (optional)

**Schema:**
```typescript
// Database: ResumeOptimizerDB
// Version: 1

// Object Store: files
interface FileStore {
  key: string;           // UUID
  sessionId: string;     // Index
  blob: Blob;            // File content
  fileName: string;
  fileType: string;
  fileSize: number;
  uploadedAt: number;
  hash: string;          // SHA-256
}

// Object Store: cache (optional)
interface CacheStore {
  key: string;           // sessionId_agentIndex
  sessionId: string;
  agentIndex: number;
  output: any;           // Agent result
  cachedAt: number;
}
```

**Implementation:**
```typescript
class IndexedDBAdapter {
  private dbName = 'ResumeOptimizerDB';
  private version = 1;
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create files store
        if (!db.objectStoreNames.contains('files')) {
          const fileStore = db.createObjectStore('files', { keyPath: 'key' });
          fileStore.createIndex('sessionId', 'sessionId', { unique: false });
          fileStore.createIndex('uploadedAt', 'uploadedAt', { unique: false });
        }

        // Create cache store
        if (!db.objectStoreNames.contains('cache')) {
          const cacheStore = db.createObjectStore('cache', { keyPath: 'key' });
          cacheStore.createIndex('sessionId', 'sessionId', { unique: false });
        }
      };
    });
  }

  async saveFile(sessionId: string, file: File): Promise<string> {
    await this.init();

    const fileKey = uuidv4();
    const hash = await this.calculateHash(file);

    const fileRecord: FileStore = {
      key: fileKey,
      sessionId,
      blob: file,
      fileName: file.name,
      fileType: file.type,
      fileSize: file.size,
      uploadedAt: Date.now(),
      hash
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['files'], 'readwrite');
      const store = transaction.objectStore('files');
      const request = store.add(fileRecord);

      request.onsuccess = () => resolve(fileKey);
      request.onerror = () => reject(request.error);
    });
  }

  async loadFile(fileKey: string): Promise<File | null> {
    await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['files'], 'readonly');
      const store = transaction.objectStore('files');
      const request = store.get(fileKey);

      request.onsuccess = () => {
        const record = request.result as FileStore | undefined;
        if (!record) {
          resolve(null);
          return;
        }

        // Reconstruct File object
        const file = new File([record.blob], record.fileName, {
          type: record.fileType,
          lastModified: record.uploadedAt
        });

        resolve(file);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async cleanupSession(sessionId: string): Promise<void> {
    await this.init();

    // Delete all files for session
    const transaction = this.db!.transaction(['files', 'cache'], 'readwrite');
    const fileStore = transaction.objectStore('files');
    const cacheStore = transaction.objectStore('cache');

    const fileIndex = fileStore.index('sessionId');
    const cacheIndex = cacheStore.index('sessionId');

    await this.deleteByIndex(fileIndex, sessionId);
    await this.deleteByIndex(cacheIndex, sessionId);
  }

  private async calculateHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}
```

#### 5.2.3 Backend Storage Strategy

**File Storage:**
- Resume files uploaded to `/uploads/{session_id}/` directory
- Original filename preserved with sanitization
- Files retained for 7 days, then cleaned up
- Symlinks to avoid duplication on retry

**Database Storage:**
- `recovery_sessions`: Full session state
- `agent_checkpoints`: Incremental agent outputs
- `error_logs`: Detailed error context
- Transaction-based updates for consistency

**Cleanup Strategy:**
```python
async def cleanup_expired_sessions():
    """Background task to cleanup expired sessions"""
    # Run every hour
    while True:
        try:
            # Find expired sessions
            expired = await db.execute(
                "SELECT session_id FROM recovery_sessions WHERE expires_at < ?"
                (datetime.now(),)
            )

            for session in expired:
                # Delete from database
                await db.execute(
                    "DELETE FROM recovery_sessions WHERE session_id = ?",
                    (session['session_id'],)
                )

                # Delete associated files
                file_path = Path(f"uploads/{session['session_id']}")
                if file_path.exists():
                    shutil.rmtree(file_path)

            await asyncio.sleep(3600)  # Sleep 1 hour

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            await asyncio.sleep(300)  # Sleep 5 minutes on error
```

### 5.3 State Capture Workflow

```typescript
class StateManager {
  private localStorageAdapter: LocalStorageAdapter;
  private indexedDBAdapter: IndexedDBAdapter;

  async captureState(context: {
    reason: string;
    errorContext?: ErrorContext;
  }): Promise<string> {
    // Generate session ID
    const sessionId = uuidv4();

    // Capture form data
    const formData = this.captureFormData();

    // Capture file
    let fileMetadata: FileMetadata | null = null;
    const file = this.getCurrentFile();

    if (file) {
      const fileKey = await this.indexedDBAdapter.saveFile(sessionId, file);
      fileMetadata = {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        indexedDBKey: fileKey,
        uploadedAt: Date.now(),
        fileHash: await this.calculateFileHash(file)
      };
    }

    // Capture processing state
    const processingState = this.captureProcessingState();

    // Build recovery session
    const session: RecoverySession = {
      sessionId,
      version: '1.0',
      createdAt: Date.now(),
      expiresAt: Date.now() + (7 * 24 * 60 * 60 * 1000), // 7 days
      formData,
      fileMetadata,
      processingState,
      errorContext: context.errorContext || null,
      recovery: {
        canAutoRetry: this.canAutoRetry(context.errorContext),
        canManualRetry: this.canManualRetry(context.errorContext),
        suggestedAction: this.getSuggestedAction(context.errorContext),
        supportReferenceId: context.errorContext?.errorId || sessionId
      }
    };

    // Save to LocalStorage
    this.localStorageAdapter.saveSession(session);

    // Notify backend (best effort)
    try {
      await this.notifyBackendStateCapture(session);
    } catch (e) {
      console.warn('Failed to notify backend of state capture', e);
    }

    return sessionId;
  }

  async restoreState(sessionId: string): Promise<void> {
    // Load from LocalStorage
    const session = this.localStorageAdapter.loadSession(sessionId);

    if (!session) {
      throw new Error('Session not found or expired');
    }

    // Restore form data
    this.restoreFormData(session.formData);

    // Restore file
    if (session.fileMetadata) {
      const file = await this.indexedDBAdapter.loadFile(
        session.fileMetadata.indexedDBKey
      );

      if (file) {
        // Verify integrity
        const hash = await this.calculateFileHash(file);
        if (hash !== session.fileMetadata.fileHash) {
          console.warn('File hash mismatch - file may be corrupted');
        }

        this.setCurrentFile(file);
      }
    }

    // Restore UI state
    this.showRecoveryBanner(session);
  }
}
```

---

## 6. Recovery Flows

### 6.1 Automatic Retry Flow

**Trigger Conditions:**
- Error category is `TRANSIENT`
- Retry count < 3
- Time since last retry > backoff period
- User has not dismissed automatic retry

**Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│                     1. Error Occurs                          │
│                  (e.g., network timeout)                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              2. ErrorHandler Classifies                      │
│                  Category: TRANSIENT                         │
│                  Retry Count: 0                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              3. StateManager Captures State                  │
│                  - Form data saved                           │
│                  - File saved to IndexedDB                   │
│                  - Session created in LocalStorage           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│          4. Show "Retrying..." Notification                  │
│                  "Network error occurred.                    │
│                   Automatically retrying in 2 seconds..."    │
│                   [Cancel] button available                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              5. Wait Exponential Backoff                     │
│                  Attempt 1: 2 seconds                        │
│                  Attempt 2: 4 seconds                        │
│                  Attempt 3: 8 seconds                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│            6. RetryCoordinator Initiates Retry               │
│                  - Sends request with session ID             │
│                  - Backend loads checkpoint                  │
│                  - Resume from last successful agent         │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌──────────────────────┐    ┌─────────────────────────┐
│   7a. Retry Success  │    │   7b. Retry Failed      │
│                      │    │                         │
│ - Continue pipeline  │    │ - Increment retry count │
│ - User sees progress │    │ - Return to step 4      │
│ - Transition to      │    │   (if count < 3)        │
│   RevealScreen       │    │ - Or go to Manual Flow  │
│                      │    │   (if count >= 3)       │
└──────────────────────┘    └─────────────────────────┘
```

**Implementation:**

```typescript
class RetryCoordinator {
  private maxAutoRetries = 3;

  async handleTransientError(
    sessionId: string,
    error: ErrorContext
  ): Promise<boolean> {
    const session = await stateManager.loadSession(sessionId);

    if (!session) {
      console.error('Session not found for retry');
      return false;
    }

    // Check retry limit
    if (session.errorContext!.retryCount >= this.maxAutoRetries) {
      return this.transitionToManualRetry(session);
    }

    // Calculate backoff
    const backoffMs = Math.pow(2, session.errorContext!.retryCount) * 1000;

    // Show notification
    notificationService.show({
      type: 'info',
      title: 'Retrying automatically...',
      message: `Network error occurred. Retrying in ${backoffMs / 1000}s...`,
      dismissible: true,
      actions: [
        {
          label: 'Cancel',
          onClick: () => this.cancelAutoRetry(sessionId)
        }
      ]
    });

    // Wait backoff period
    await this.sleep(backoffMs);

    // Check if retry was cancelled
    if (this.isRetryCancelled(sessionId)) {
      return this.transitionToManualRetry(session);
    }

    // Attempt retry
    try {
      const result = await this.executeRetry(session);

      // Success - cleanup and continue
      await stateManager.cleanupSession(sessionId);
      notificationService.dismiss();

      return true;

    } catch (retryError) {
      // Retry failed - update session and recurse
      session.errorContext!.retryCount++;
      session.errorContext!.lastRetryAt = Date.now();
      await stateManager.saveSession(session);

      // Classify new error
      const newCategory = errorHandler.classify(retryError);

      if (newCategory === 'TRANSIENT' &&
          session.errorContext!.retryCount < this.maxAutoRetries) {
        // Try again
        return this.handleTransientError(sessionId, {
          ...session.errorContext!,
          retryCount: session.errorContext!.retryCount
        });
      } else {
        // Give up on auto-retry
        return this.transitionToManualRetry(session);
      }
    }
  }

  private async executeRetry(session: RecoverySession): Promise<any> {
    // Send retry request to backend
    const response = await apiClient.post('/api/optimize-retry', {
      sessionId: session.sessionId,
      checkpointId: session.processingState.lastCheckpointId,
      resumeFromAgent: session.processingState.currentAgent
    });

    return response.data;
  }
}
```

### 6.2 Manual Retry Flow

**Trigger Conditions:**
- Error category is `RECOVERABLE` or `PERMANENT`
- Automatic retry failed 3 times
- User clicked "Cancel" on automatic retry
- User returned to site after closing browser

**Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│              1. User Lands on InputScreen                    │
│                  (After error or page reload)                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│          2. StateManager Checks for Recovery                 │
│                  - Check LocalStorage for sessions           │
│                  - Find most recent non-expired session      │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌──────────────────────┐    ┌─────────────────────────┐
│  3a. Session Found   │    │ 3b. No Session          │
│                      │    │                         │
│ - Load session data  │    │ - Show normal input UI  │
│ - Restore form/file  │    │ - No recovery banner    │
│ - Show banner        │    │                         │
└──────┬───────────────┘    └─────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│             4. Display Recovery Banner                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ ⚠️  Error Occurred During Processing                │     │
│  │                                                      │     │
│  │ Your data from 5 minutes ago has been preserved.    │     │
│  │                                                      │     │
│  │ Error: Network connection lost while processing     │     │
│  │ job analysis.                                        │     │
│  │                                                      │     │
│  │ [Retry Processing]  [Start Fresh]  [Details]        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
       │
       │ User clicks "Retry Processing"
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│            5. Validate Current State                         │
│                  - Verify file still valid                   │
│                  - Verify form data complete                 │
│                  - Check backend session exists              │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌──────────────────────┐    ┌─────────────────────────┐
│  6a. Validation OK   │    │ 6b. Validation Failed   │
│                      │    │                         │
│ - Send retry request │    │ - Show error message    │
│ - Include session ID │    │ - Offer to start fresh  │
└──────┬───────────────┘    └─────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│         7. Backend Processes Retry Request                   │
│                  - Load recovery session from DB             │
│                  - Check for checkpoints                     │
│                  - Resume pipeline or start fresh            │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌──────────────────────┐    ┌─────────────────────────┐
│  8a. Resume Success  │    │   8b. Resume Failed     │
│                      │    │                         │
│ - Continue to        │    │ - Try fallback strategy │
│   ProcessingScreen   │    │ - Or restart pipeline   │
│ - Show progress      │    │   from beginning        │
│ - Complete normally  │    │                         │
└──────────────────────┘    └──────┬──────────────────┘
                                   │
                                   ▼
                        ┌─────────────────────────┐
                        │   9. Final Failure      │
                        │                         │
                        │ - Show detailed error   │
                        │ - Provide support info  │
                        │ - Preserve state        │
                        └─────────────────────────┘
```

**Implementation:**

```typescript
// InputScreen component
export default function InputScreen() {
  const [recoverySession, setRecoverySession] =
    useState<RecoverySession | null>(null);

  useEffect(() => {
    // Check for recovery session on mount
    const checkRecovery = async () => {
      const session = await stateManager.findLatestSession();
      if (session) {
        setRecoverySession(session);
        await stateManager.restoreState(session.sessionId);
      }
    };

    checkRecovery();
  }, []);

  const handleRetry = async () => {
    if (!recoverySession) return;

    try {
      // Validate state
      const isValid = await validateRecoveryState(recoverySession);
      if (!isValid) {
        showError('Session data is no longer valid. Please start fresh.');
        return;
      }

      // Show loading
      setIsRetrying(true);

      // Send retry request
      const response = await apiClient.post('/api/optimize-retry', {
        sessionId: recoverySession.sessionId,
        formData: recoverySession.formData,
        // File is retrieved from IndexedDB by backend via session ID
      });

      // Transition to processing screen
      navigate('/processing', {
        state: {
          applicationId: response.data.applicationId,
          isRetry: true,
          sessionId: recoverySession.sessionId
        }
      });

    } catch (error) {
      setIsRetrying(false);
      showError('Retry failed. Please try again or start fresh.');
    }
  };

  const handleStartFresh = async () => {
    if (!recoverySession) return;

    // Confirm with user
    const confirmed = await confirmDialog({
      title: 'Start Fresh?',
      message: 'This will discard your preserved data. Are you sure?',
      confirmText: 'Start Fresh',
      cancelText: 'Cancel'
    });

    if (confirmed) {
      await stateManager.cleanupSession(recoverySession.sessionId);
      setRecoverySession(null);
      // Reset form
      resetForm();
    }
  };

  return (
    <div>
      {/* Recovery Banner */}
      {recoverySession && (
        <RecoveryBanner
          session={recoverySession}
          onRetry={handleRetry}
          onStartFresh={handleStartFresh}
          isRetrying={isRetrying}
        />
      )}

      {/* Normal form UI */}
      <FormUI />
    </div>
  );
}
```

**RecoveryBanner Component:**

```typescript
function RecoveryBanner({
  session,
  onRetry,
  onStartFresh,
  isRetrying
}: RecoveryBannerProps) {
  const [showDetails, setShowDetails] = useState(false);

  const errorMessage = session.errorContext?.errorMessage ||
    'An error occurred during processing';

  const timeAgo = formatTimeAgo(session.createdAt);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6"
    >
      <div className="flex items-start">
        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />

        <div className="ml-3 flex-1">
          <h3 className="text-sm font-semibold text-yellow-900">
            Error Occurred During Processing
          </h3>

          <p className="text-sm text-yellow-800 mt-1">
            Your data from <strong>{timeAgo}</strong> has been preserved.
          </p>

          <p className="text-sm text-yellow-700 mt-2">
            {errorMessage}
          </p>

          {showDetails && session.errorContext && (
            <div className="mt-3 p-3 bg-yellow-100 rounded text-xs font-mono text-yellow-900">
              <div>Error ID: {session.errorContext.errorId}</div>
              <div>Type: {session.errorContext.errorType}</div>
              <div>Occurred: {new Date(session.errorContext.occurredAt).toLocaleString()}</div>
              {session.errorContext.retryCount > 0 && (
                <div>Retry Attempts: {session.errorContext.retryCount}</div>
              )}
            </div>
          )}

          <div className="mt-4 flex gap-3">
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
            >
              {isRetrying ? 'Retrying...' : 'Retry Processing'}
            </button>

            <button
              onClick={onStartFresh}
              disabled={isRetrying}
              className="px-4 py-2 bg-white border border-yellow-600 text-yellow-700 rounded hover:bg-yellow-50"
            >
              Start Fresh
            </button>

            <button
              onClick={() => setShowDetails(!showDetails)}
              className="px-3 py-2 text-yellow-700 hover:text-yellow-900 text-sm"
            >
              {showDetails ? 'Hide' : 'Show'} Details
            </button>
          </div>

          <p className="text-xs text-yellow-600 mt-3">
            Support Reference: {session.recovery.supportReferenceId}
          </p>
        </div>

        <button
          onClick={() => onStartFresh()}
          className="text-yellow-600 hover:text-yellow-800"
          title="Dismiss and start fresh"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </motion.div>
  );
}
```

### 6.3 Backend Recovery Endpoint

```python
@app.post("/api/optimize-retry")
async def optimize_retry(
    request: Request,
    session_id: str = Body(...),
    form_data: dict = Body(None),
):
    """Handle retry request with session recovery"""

    # Load recovery session
    recovery_session = await db.get_recovery_session(session_id)

    if not recovery_session:
        raise HTTPException(
            status_code=404,
            detail="Recovery session not found or expired"
        )

    # Check if we can resume from checkpoint
    checkpoints = await db.get_agent_checkpoints(session_id)

    if checkpoints:
        # Resume from last checkpoint
        logger.info(
            f"Resuming session {session_id} from agent {len(checkpoints)}"
        )

        result = await resume_pipeline_from_checkpoint(
            session_id=session_id,
            checkpoints=checkpoints,
            recovery_session=recovery_session
        )
    else:
        # No checkpoints - start fresh with preserved data
        logger.info(f"Restarting session {session_id} from beginning")

        # Use form data from request or recovery session
        input_data = form_data or json.loads(recovery_session['form_data'])

        # Retrieve file from storage
        file_path = Path(f"uploads/{session_id}") / recovery_session['file_metadata']['fileName']

        if not file_path.exists():
            raise HTTPException(
                status_code=400,
                detail="Original file not found. Please re-upload."
            )

        result = await start_optimization_pipeline(
            session_id=session_id,
            input_data=input_data,
            file_path=file_path
        )

    # Update recovery session status
    await db.update_recovery_session(
        session_id=session_id,
        status='recovered'
    )

    return {
        "success": True,
        "applicationId": result['application_id'],
        "resumedFromAgent": len(checkpoints) if checkpoints else 0
    }


async def resume_pipeline_from_checkpoint(
    session_id: str,
    checkpoints: List[dict],
    recovery_session: dict
) -> dict:
    """Resume agent pipeline from last checkpoint"""

    # Reconstruct state from checkpoints
    agent_outputs = {
        checkpoint['agent_index']: json.loads(checkpoint['agent_output'])
        for checkpoint in checkpoints
    }

    # Determine which agent to start from
    last_completed = max(agent_outputs.keys())
    start_from = last_completed + 1

    if start_from >= len(AGENT_PIPELINE):
        # All agents completed - this shouldn't happen
        logger.warning(f"All agents completed for {session_id} but marked as failed")
        # Return existing result
        application = await db.get_application_by_session(session_id)
        return {"application_id": application['id']}

    # Execute remaining agents
    logger.info(f"Executing agents {start_from} to {len(AGENT_PIPELINE) - 1}")

    current_state = agent_outputs

    for i in range(start_from, len(AGENT_PIPELINE)):
        agent = AGENT_PIPELINE[i]

        try:
            # Execute agent with previous outputs
            result = await agent.run(
                previous_outputs=current_state,
                session_id=session_id
            )

            # Save checkpoint
            await db.save_agent_checkpoint(
                session_id=session_id,
                agent_index=i,
                agent_name=agent.name,
                agent_output=result
            )

            current_state[i] = result

        except Exception as e:
            # Checkpoint and re-raise
            await db.update_recovery_session(
                session_id=session_id,
                status='failed',
                current_agent=i,
                error_message=str(e)
            )
            raise

    # All agents completed - save final result
    application_id = await db.save_application_result(
        session_id=session_id,
        outputs=current_state
    )

    return {"application_id": application_id}
```

---

## 7. Implementation Details

### 7.1 Phase 1: Foundation (Week 1-2)

**Goals:**
- Database schema setup
- Basic state capture/restoration
- Error classification framework

**Tasks:**

1. **Database Migration**
   - Create `recovery_sessions` table
   - Create `agent_checkpoints` table
   - Create `error_logs` table
   - Add indexes for performance
   - Create cleanup procedures

2. **Frontend Storage Layer**
   - Implement `LocalStorageAdapter`
   - Implement `IndexedDBAdapter`
   - Implement `StateManager` singleton
   - Add storage quota handling
   - Add encryption for sensitive data

3. **Error Classification**
   - Create `ErrorCategory` enum
   - Implement `classify_error()` function
   - Create error message mapping
   - Add user-friendly descriptions

4. **Basic State Capture**
   - Capture form data on error
   - Store in LocalStorage
   - Add session expiration (7 days)
   - Implement cleanup on mount

**Acceptance Criteria:**
- State persists across page refresh
- Old sessions auto-expire
- Error classification 90%+ accurate
- Database tables properly indexed

### 7.2 Phase 2: File Handling (Week 3)

**Goals:**
- Preserve uploaded resume files
- Handle large files efficiently
- Implement file integrity checks

**Tasks:**

1. **IndexedDB Integration**
   - Implement file storage in IndexedDB
   - Add file hash calculation (SHA-256)
   - Implement integrity verification
   - Add quota exceeded handling

2. **Backend File Storage**
   - Save uploaded files to session directory
   - Preserve files on pipeline failure
   - Implement file cleanup cron job
   - Add symlinks to avoid duplication

3. **File Restoration**
   - Load file from IndexedDB
   - Reconstruct File object
   - Update file input UI
   - Show file preview

**Acceptance Criteria:**
- Files up to 10MB stored successfully
- File integrity verified on restore
- No file duplication on retry
- Graceful handling of storage quota

### 7.3 Phase 3: Checkpointing (Week 4)

**Goals:**
- Save agent outputs incrementally
- Enable resume from failure point
- Minimize redundant processing

**Tasks:**

1. **Agent Instrumentation**
   - Add checkpoint after each agent
   - Store output in `agent_checkpoints`
   - Include execution metadata
   - Handle checkpoint failures gracefully

2. **Pipeline Resume Logic**
   - Load checkpoints from database
   - Reconstruct state for resume
   - Skip completed agents
   - Pass outputs to next agent

3. **Streaming Integration**
   - Send checkpoint events via SSE
   - Update frontend progress indicator
   - Show recovery point in UI

**Acceptance Criteria:**
- Each agent creates checkpoint on success
- Pipeline resumes from last checkpoint
- No duplicate agent execution
- Checkpoint overhead < 100ms per agent

### 7.4 Phase 4: Retry Mechanisms (Week 5-6)

**Goals:**
- Automatic retry for transient errors
- Manual retry UI
- Exponential backoff strategy

**Tasks:**

1. **Automatic Retry**
   - Implement `RetryCoordinator`
   - Add exponential backoff (2^n seconds)
   - Limit to 3 auto-retries
   - Show retry notification UI

2. **Manual Retry Flow**
   - Add recovery banner to InputScreen
   - Implement "Retry Processing" button
   - Add "Start Fresh" confirmation
   - Show error details modal

3. **Backend Retry Endpoint**
   - Create `/api/optimize-retry` endpoint
   - Load recovery session from DB
   - Resume from checkpoint or restart
   - Update recovery status

4. **Fallback Strategies**
   - Try alternative LLM model on failure
   - Reduce context length if exceeded
   - Skip optional processing steps

**Acceptance Criteria:**
- Transient errors retry automatically
- User can manually retry from preserved state
- Fallback model used on repeated failures
- Recovery banner shows clear messaging

### 7.5 Phase 5: UX Polish (Week 7)

**Goals:**
- User-friendly error messages
- Visual feedback for preserved state
- Support reference IDs

**Tasks:**

1. **Error Messaging**
   - Create error message templates
   - Map error types to user descriptions
   - Add actionable next steps
   - Include estimated recovery time

2. **Recovery Banner**
   - Design polished banner UI
   - Show time since error ("5 minutes ago")
   - Display file preview
   - Add support reference ID

3. **Progress Indicators**
   - Show "Retrying..." state
   - Display retry countdown
   - Show checkpoint progress
   - Animate state transitions

4. **Notifications**
   - Success notification on recovery
   - Warning for quota issues
   - Info for automatic retry
   - Error for permanent failures

**Acceptance Criteria:**
- Error messages clear and actionable
- Recovery banner visually appealing
- Users understand state preservation
- Support can reference error IDs

### 7.6 Phase 6: Testing & Monitoring (Week 8)

**Goals:**
- Comprehensive test coverage
- Monitoring and alerting
- Performance validation

**Tasks:**

1. **Unit Tests**
   - Test state capture/restoration
   - Test error classification
   - Test retry logic
   - Test storage adapters

2. **Integration Tests**
   - Test end-to-end recovery flow
   - Test checkpoint resume
   - Test file preservation
   - Test cross-browser compatibility

3. **Chaos Testing**
   - Simulate network failures
   - Simulate agent crashes
   - Simulate storage quota exceeded
   - Simulate browser crashes

4. **Monitoring Setup**
   - Add error rate metrics
   - Track recovery success rate
   - Monitor storage usage
   - Alert on repeated failures

**Acceptance Criteria:**
- 80%+ unit test coverage
- All recovery flows tested
- Chaos tests pass consistently
- Monitoring dashboard operational

---

## 8. Security Considerations

### 8.1 Data Protection

**Sensitive Data Identification:**
- Resume files (PII: name, contact, work history)
- Job posting URLs (potential internal URLs)
- Session IDs (must be cryptographically secure)
- Error context (may contain PII in error messages)

**Protection Measures:**

1. **Encryption at Rest**
```typescript
class CryptoAdapter {
  private async getKey(): Promise<CryptoKey> {
    // Derive key from session-specific salt
    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(this.sessionId),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    return window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  async encryptBlob(blob: Blob): Promise<EncryptedBlob> {
    const key = await this.getKey();
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const data = await blob.arrayBuffer();

    const encrypted = await window.crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    );

    return {
      data: encrypted,
      iv: iv.buffer,
      algorithm: 'AES-GCM'
    };
  }
}
```

2. **Sanitization**
```python
def sanitize_error_message(error: Exception) -> str:
    """Remove PII from error messages"""
    message = str(error)

    # Remove email addresses
    message = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', message)

    # Remove phone numbers
    message = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', message)

    # Remove file paths (may contain usernames)
    message = re.sub(r'[A-Za-z]:\\(?:[^\\\/:*?"<>|\r\n]+\\)*[^\\\/:*?"<>|\r\n]*', '[PATH]', message)

    # Remove IP addresses
    message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', message)

    return message
```

3. **Session Security**
```typescript
// Generate cryptographically secure session IDs
function generateSessionId(): string {
  const array = new Uint8Array(16);
  window.crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Validate session ID format (prevent injection)
function isValidSessionId(sessionId: string): boolean {
  return /^[a-f0-9]{32}$/.test(sessionId);
}
```

### 8.2 XSS Prevention

**User Input Sanitization:**
```typescript
class InputSanitizer {
  sanitizeJobPosting(input: string): string {
    // Use DOMPurify for HTML sanitization
    return DOMPurify.sanitize(input, {
      ALLOWED_TAGS: [], // No HTML allowed
      KEEP_CONTENT: true
    });
  }

  sanitizeFormData(data: any): any {
    if (typeof data === 'string') {
      return this.sanitizeJobPosting(data);
    }

    if (typeof data === 'object') {
      const sanitized: any = {};
      for (const [key, value] of Object.entries(data)) {
        sanitized[key] = this.sanitizeFormData(value);
      }
      return sanitized;
    }

    return data;
  }
}
```

**Safe Rendering:**
```typescript
// Never use dangerouslySetInnerHTML with user input
function ErrorMessage({ message }: { message: string }) {
  // Safe - React escapes by default
  return <p>{message}</p>;

  // UNSAFE - Don't do this
  // return <p dangerouslySetInnerHTML={{ __html: message }} />;
}
```

### 8.3 Access Control

**Backend Authorization:**
```python
async def verify_session_ownership(session_id: str, request: Request) -> bool:
    """Verify user owns the session"""
    # In future with auth: check user_id matches session owner
    # For now: check session exists and not expired

    session = await db.get_recovery_session(session_id)

    if not session:
        return False

    if datetime.now() > session['expires_at']:
        return False

    # Could check IP address match (basic protection)
    if session.get('ip_address') != request.client.host:
        logger.warning(f"IP mismatch for session {session_id}")
        # Allow but log - IP can change legitimately

    return True


@app.post("/api/optimize-retry")
async def optimize_retry(request: Request, session_id: str = Body(...)):
    # Verify ownership
    if not await verify_session_ownership(session_id, request):
        raise HTTPException(status_code=403, detail="Access denied")

    # ... rest of handler
```

### 8.4 Rate Limiting

**Prevent Abuse:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/optimize-retry")
@limiter.limit("5/minute")  # Max 5 retries per minute per IP
async def optimize_retry(request: Request, ...):
    # ... handler
```

### 8.5 File Upload Security

**Validation:**
```python
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload(file: UploadFile) -> None:
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {ext} not allowed")

    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File too large (max 10MB)")

    # Check magic bytes (file signature)
    magic = content[:8]
    if not is_valid_file_signature(magic, ext):
        raise ValueError("File content doesn't match extension")

    # Reset file pointer
    await file.seek(0)
```

---

## 9. Performance Considerations

### 9.1 Performance Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| State capture time | < 200ms | 500ms |
| State restoration time | < 500ms | 1s |
| File storage (IndexedDB) | < 1s for 5MB | 3s |
| File retrieval (IndexedDB) | < 500ms | 1s |
| Checkpoint creation | < 50ms | 100ms |
| LocalStorage read/write | < 10ms | 50ms |
| Session cleanup (cron) | < 5s per 100 sessions | 30s |

### 9.2 Optimization Strategies

#### 9.2.1 Lazy Loading

```typescript
// Don't load IndexedDB until needed
class StateManager {
  private indexedDBAdapter: IndexedDBAdapter | null = null;

  private async getIndexedDBAdapter(): Promise<IndexedDBAdapter> {
    if (!this.indexedDBAdapter) {
      this.indexedDBAdapter = new IndexedDBAdapter();
      await this.indexedDBAdapter.init();
    }
    return this.indexedDBAdapter;
  }

  async captureState(context: any): Promise<string> {
    // Capture form data synchronously
    const formData = this.captureFormData();
    const sessionId = uuidv4();

    // Save to LocalStorage immediately
    this.localStorageAdapter.saveSession({
      sessionId,
      formData,
      // ... other non-file data
    });

    // Save file asynchronously (don't block)
    const file = this.getCurrentFile();
    if (file) {
      this.saveFileAsync(sessionId, file).catch(error => {
        console.error('Failed to save file to IndexedDB', error);
      });
    }

    return sessionId;
  }
}
```

#### 9.2.2 Compression

```typescript
// Compress large form data
class CompressionAdapter {
  async compress(data: string): Promise<ArrayBuffer> {
    const blob = new Blob([data]);
    const stream = blob.stream();
    const compressedStream = stream.pipeThrough(
      new CompressionStream('gzip')
    );
    const compressedBlob = await new Response(compressedStream).blob();
    return compressedBlob.arrayBuffer();
  }

  async decompress(data: ArrayBuffer): Promise<string> {
    const blob = new Blob([data]);
    const stream = blob.stream();
    const decompressedStream = stream.pipeThrough(
      new DecompressionStream('gzip')
    );
    const decompressedBlob = await new Response(decompressedStream).blob();
    return decompressedBlob.text();
  }
}

// Use for large job postings
if (jobPosting.length > 10000) {
  formData.jobPostingCompressed = await compressionAdapter.compress(jobPosting);
  formData.jobPosting = undefined; // Remove uncompressed
}
```

#### 9.2.3 Debouncing

```typescript
// Debounce form state capture during typing
class StateManager {
  private captureDebounceTimer: number | null = null;

  debouncedCapture(context: any): void {
    if (this.captureDebounceTimer) {
      clearTimeout(this.captureDebounceTimer);
    }

    this.captureDebounceTimer = window.setTimeout(() => {
      this.captureState(context);
    }, 500); // Wait 500ms after last change
  }
}

// Use in form onChange
<textarea
  onChange={(e) => {
    setJobPosting(e.target.value);
    stateManager.debouncedCapture({ reason: 'form_change' });
  }}
/>
```

#### 9.2.4 Batch Operations

```python
# Batch checkpoint saves
class CheckpointBatcher:
    def __init__(self, db: Database):
        self.db = db
        self.pending_checkpoints: List[dict] = []
        self.batch_size = 10
        self.flush_interval = 5  # seconds

    async def add_checkpoint(self, checkpoint: dict):
        self.pending_checkpoints.append(checkpoint)

        if len(self.pending_checkpoints) >= self.batch_size:
            await self.flush()

    async def flush(self):
        if not self.pending_checkpoints:
            return

        # Insert all at once
        await self.db.executemany(
            "INSERT INTO agent_checkpoints (...) VALUES (...)",
            self.pending_checkpoints
        )

        self.pending_checkpoints.clear()
```

#### 9.2.5 Indexing

```sql
-- Optimize common queries
CREATE INDEX idx_recovery_session_status
  ON recovery_sessions(status, expires_at);

CREATE INDEX idx_checkpoint_lookup
  ON agent_checkpoints(session_id, agent_index);

CREATE INDEX idx_error_recent
  ON error_logs(created_at DESC, error_category);

-- Partial index for active sessions only
CREATE INDEX idx_recovery_active
  ON recovery_sessions(session_id)
  WHERE status IN ('pending', 'processing', 'failed');
```

### 9.3 Memory Management

```typescript
// Clear large objects after use
class StateManager {
  private fileCache = new Map<string, File>();
  private readonly MAX_CACHE_SIZE = 5;

  async loadFile(sessionId: string): Promise<File | null> {
    // Check cache first
    if (this.fileCache.has(sessionId)) {
      return this.fileCache.get(sessionId)!;
    }

    // Load from IndexedDB
    const adapter = await this.getIndexedDBAdapter();
    const file = await adapter.loadFile(sessionId);

    if (file) {
      // Add to cache
      this.fileCache.set(sessionId, file);

      // Evict oldest if cache full
      if (this.fileCache.size > this.MAX_CACHE_SIZE) {
        const firstKey = this.fileCache.keys().next().value;
        this.fileCache.delete(firstKey);
      }
    }

    return file;
  }

  clearCache(): void {
    this.fileCache.clear();
  }
}

// Clear cache on navigation
useEffect(() => {
  return () => {
    stateManager.clearCache();
  };
}, []);
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Frontend:**

```typescript
// StateManager tests
describe('StateManager', () => {
  let stateManager: StateManager;

  beforeEach(() => {
    localStorage.clear();
    stateManager = new StateManager();
  });

  it('should capture form state', async () => {
    const mockFormData = {
      jobPosting: 'Software Engineer...',
      isJobUrl: false
    };

    const sessionId = await stateManager.captureState({
      formData: mockFormData,
      reason: 'test'
    });

    expect(sessionId).toMatch(/^[a-f0-9]{32}$/);

    const session = await stateManager.loadSession(sessionId);
    expect(session?.formData).toEqual(mockFormData);
  });

  it('should expire old sessions', async () => {
    const sessionId = await stateManager.captureState({
      formData: {},
      reason: 'test'
    });

    // Manually set expiration to past
    const session = await stateManager.loadSession(sessionId);
    session!.expiresAt = Date.now() - 1000;
    await stateManager.saveSession(session!);

    const loaded = await stateManager.loadSession(sessionId);
    expect(loaded).toBeNull();
  });

  it('should handle storage quota exceeded', async () => {
    // Mock localStorage quota error
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = jest.fn(() => {
      throw new DOMException('QuotaExceededError');
    });

    await expect(async () => {
      await stateManager.captureState({
        formData: { jobPosting: 'x'.repeat(10_000_000) },
        reason: 'test'
      });
    }).rejects.toThrow();

    localStorage.setItem = originalSetItem;
  });
});

// IndexedDB tests
describe('IndexedDBAdapter', () => {
  let adapter: IndexedDBAdapter;

  beforeEach(async () => {
    adapter = new IndexedDBAdapter();
    await adapter.init();
  });

  it('should store and retrieve files', async () => {
    const file = new File(['test content'], 'resume.pdf', {
      type: 'application/pdf'
    });

    const sessionId = 'test-session';
    const fileKey = await adapter.saveFile(sessionId, file);

    const retrieved = await adapter.loadFile(fileKey);
    expect(retrieved?.name).toBe('resume.pdf');
    expect(retrieved?.size).toBe(file.size);

    const content = await retrieved?.text();
    expect(content).toBe('test content');
  });

  it('should verify file integrity', async () => {
    const file = new File(['test content'], 'resume.pdf');
    const hash1 = await adapter.calculateHash(file);
    const hash2 = await adapter.calculateHash(file);

    expect(hash1).toBe(hash2);

    const differentFile = new File(['different'], 'resume.pdf');
    const hash3 = await adapter.calculateHash(differentFile);

    expect(hash1).not.toBe(hash3);
  });
});
```

**Backend:**

```python
# Recovery service tests
@pytest.mark.asyncio
async def test_create_recovery_session(db_session):
    session_id = str(uuid.uuid4())

    await recovery_service.create_session(
        session_id=session_id,
        form_data={"job_posting": "Software Engineer"},
        file_metadata={"file_name": "resume.pdf"}
    )

    session = await db_session.get_recovery_session(session_id)
    assert session is not None
    assert session['session_id'] == session_id


@pytest.mark.asyncio
async def test_checkpoint_creation(db_session):
    session_id = str(uuid.uuid4())
    await recovery_service.create_session(session_id, {}, {})

    await recovery_service.save_checkpoint(
        session_id=session_id,
        agent_index=0,
        agent_name="JobAnalyzer",
        agent_output={"keywords": ["Python", "API"]}
    )

    checkpoints = await db_session.get_agent_checkpoints(session_id)
    assert len(checkpoints) == 1
    assert checkpoints[0]['agent_name'] == "JobAnalyzer"


@pytest.mark.asyncio
async def test_resume_from_checkpoint(db_session, mock_agents):
    session_id = str(uuid.uuid4())
    await recovery_service.create_session(session_id, {}, {})

    # Create checkpoints for agents 0-2
    for i in range(3):
        await recovery_service.save_checkpoint(
            session_id=session_id,
            agent_index=i,
            agent_name=f"Agent{i}",
            agent_output={"result": i}
        )

    # Resume should start from agent 3
    result = await recovery_service.resume_pipeline(session_id)

    # Verify agents 0-2 were not called again
    assert mock_agents[0].call_count == 0
    assert mock_agents[1].call_count == 0
    assert mock_agents[2].call_count == 0

    # Verify agents 3-4 were called
    assert mock_agents[3].call_count == 1
    assert mock_agents[4].call_count == 1


def test_error_classification():
    # Transient errors
    assert classify_error(TimeoutError()) == 'TRANSIENT'
    assert classify_error(httpx.TimeoutException()) == 'TRANSIENT'

    # Recoverable errors
    assert classify_error(LLMError(status_code=500)) == 'RECOVERABLE'
    assert classify_error(AgentProcessingError()) == 'RECOVERABLE'

    # Permanent errors
    assert classify_error(AuthenticationError()) == 'PERMANENT'
    assert classify_error(ConfigurationError()) == 'PERMANENT'
```

### 10.2 Integration Tests

```typescript
// End-to-end recovery flow
describe('Recovery Flow Integration', () => {
  let app: AppInstance;

  beforeEach(async () => {
    app = await createTestApp();
  });

  it('should recover from network failure', async () => {
    // 1. User fills form
    await app.fillInput('jobPosting', 'Software Engineer position...');
    await app.uploadFile('resume.pdf');

    // 2. Start processing
    await app.clickSubmit();
    await app.waitForScreen('processing');

    // 3. Simulate network failure after agent 2
    server.simulateNetworkError({ afterAgent: 2 });

    // 4. Should redirect to input screen
    await app.waitForScreen('input');

    // 5. Recovery banner should be visible
    const banner = await app.findRecoveryBanner();
    expect(banner).toBeVisible();
    expect(banner.text()).toContain('Network error');

    // 6. Form should be pre-filled
    expect(await app.getInputValue('jobPosting')).toBe('Software Engineer position...');
    expect(await app.getFileName()).toBe('resume.pdf');

    // 7. Click retry
    await app.clickRetry();
    await app.waitForScreen('processing');

    // 8. Should resume from agent 3
    const progress = await app.getProgress();
    expect(progress.completedAgents).toEqual([0, 1, 2]);
    expect(progress.currentAgent).toBe(3);

    // 9. Complete successfully
    await app.waitForScreen('reveal');
  });

  it('should handle page refresh during processing', async () => {
    // 1. Start processing
    await app.fillInput('jobPosting', 'Test job');
    await app.uploadFile('resume.pdf');
    await app.clickSubmit();

    // 2. Wait for agent 2 to complete
    await app.waitForAgentComplete(2);

    // 3. Refresh page
    await app.refresh();

    // 4. Should reconnect and continue
    await app.waitForScreen('processing');
    const progress = await app.getProgress();
    expect(progress.completedAgents).toContain(0, 1, 2);
  });

  it('should handle browser close and reopen', async () => {
    // 1. Start processing
    const sessionId = await app.startProcessing({
      jobPosting: 'Test job',
      file: 'resume.pdf'
    });

    // 2. Simulate agent failure
    server.simulateAgentError({ agent: 3 });
    await app.waitForScreen('input');

    // 3. Close browser
    await app.close();

    // 4. Reopen browser
    app = await createTestApp();
    await app.navigate('/');

    // 5. Recovery banner should appear
    const banner = await app.findRecoveryBanner();
    expect(banner).toBeVisible();

    // 6. Data should be preserved
    expect(await app.getInputValue('jobPosting')).toBe('Test job');
  });
});
```

### 10.3 Chaos Testing

```python
# Chaos test scenarios
import pytest
import asyncio
import random

@pytest.mark.chaos
@pytest.mark.asyncio
async def test_random_network_failures():
    """Simulate random network failures during pipeline"""

    for iteration in range(100):
        session_id = str(uuid.uuid4())

        # Random failure point
        fail_at_agent = random.randint(0, 4)

        # Start pipeline
        result = await run_pipeline_with_chaos(
            session_id=session_id,
            chaos_scenario={
                'type': 'network_failure',
                'fail_at_agent': fail_at_agent,
                'probability': 0.5  # 50% chance per agent
            }
        )

        # Recovery should work
        if result['status'] == 'failed':
            # Verify session was saved
            session = await db.get_recovery_session(session_id)
            assert session is not None

            # Verify checkpoints exist
            checkpoints = await db.get_agent_checkpoints(session_id)
            assert len(checkpoints) >= fail_at_agent

            # Retry should succeed
            retry_result = await recovery_service.resume_pipeline(session_id)
            assert retry_result['status'] == 'success'


@pytest.mark.chaos
@pytest.mark.asyncio
async def test_storage_failures():
    """Simulate storage failures during state capture"""

    # Mock IndexedDB to fail randomly
    with mock_storage_failures(probability=0.3):
        for i in range(50):
            try:
                session_id = await state_manager.capture_state({
                    'formData': {'jobPosting': 'x' * 10000},
                    'file': create_test_file(size=5_000_000)
                })

                # If capture succeeded, verify data
                session = await state_manager.load_session(session_id)
                assert session is not None

            except StorageError:
                # Storage failure is expected - should be logged
                pass


@pytest.mark.chaos
@pytest.mark.asyncio
async def test_concurrent_sessions():
    """Test multiple concurrent sessions with failures"""

    async def run_session():
        session_id = str(uuid.uuid4())

        try:
            result = await run_pipeline_with_chaos(
                session_id=session_id,
                chaos_scenario={
                    'type': 'random',
                    'failure_rate': 0.2
                }
            )

            if result['status'] == 'failed':
                # Retry
                await asyncio.sleep(random.uniform(0.1, 1.0))
                retry_result = await recovery_service.resume_pipeline(session_id)
                return retry_result['status']

            return result['status']

        except Exception as e:
            logger.error(f"Session {session_id} failed: {e}")
            return 'error'

    # Run 20 concurrent sessions
    results = await asyncio.gather(*[run_session() for _ in range(20)])

    # All should eventually succeed
    success_count = sum(1 for r in results if r == 'success')
    assert success_count >= 18  # Allow 10% failure rate
```

### 10.4 Performance Tests

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_state_capture_performance():
    """Verify state capture meets performance targets"""

    form_data = {
        'jobPosting': 'x' * 50000,  # 50KB job posting
        'additionalNotes': 'Test notes'
    }

    file = create_test_file(size=5_000_000)  # 5MB file

    # Measure capture time
    start = time.time()
    session_id = await state_manager.capture_state({
        'formData': form_data,
        'file': file
    })
    duration = time.time() - start

    # Should complete within 500ms
    assert duration < 0.5, f"Capture took {duration}s (target: 0.5s)"

    # Verify data was saved
    session = await state_manager.load_session(session_id)
    assert session is not None


@pytest.mark.performance
@pytest.mark.asyncio
async def test_checkpoint_overhead():
    """Verify checkpoint creation doesn't slow down pipeline"""

    # Run pipeline without checkpointing
    start = time.time()
    await run_pipeline(session_id='test1', checkpoints_enabled=False)
    baseline_duration = time.time() - start

    # Run pipeline with checkpointing
    start = time.time()
    await run_pipeline(session_id='test2', checkpoints_enabled=True)
    checkpoint_duration = time.time() - start

    overhead = checkpoint_duration - baseline_duration

    # Overhead should be < 500ms total (5 agents * 100ms)
    assert overhead < 0.5, f"Checkpoint overhead {overhead}s (target: <0.5s)"
```

---

## 11. Rollout Plan

### 11.1 Rollout Strategy

**Approach:** Progressive rollout with feature flags

**Phases:**

1. **Internal Testing (Week 8)**
   - Deploy to staging environment
   - Team testing for 1 week
   - Fix critical bugs
   - Validate all recovery scenarios

2. **Beta Release (Week 9)**
   - Enable for 10% of users via feature flag
   - Monitor error rates and recovery success
   - Collect user feedback
   - Performance validation

3. **Gradual Rollout (Week 10-11)**
   - Increase to 25% of users
   - Increase to 50% of users
   - Increase to 100% of users
   - Monitor metrics at each stage

4. **Feature Flag Removal (Week 12)**
   - Remove feature flag
   - Make error handling system permanent
   - Archive old code

### 11.2 Monitoring & Metrics

**Key Metrics:**

```typescript
interface ErrorHandlingMetrics {
  // Error rates
  totalErrors: number;
  errorsByCategory: {
    TRANSIENT: number;
    RECOVERABLE: number;
    PERMANENT: number;
  };
  errorsByAgent: Record<string, number>;

  // Recovery rates
  autoRetryAttempts: number;
  autoRetrySuccesses: number;
  autoRetryFailures: number;
  manualRetryAttempts: number;
  manualRetrySuccesses: number;

  // State preservation
  sessionsCaptured: number;
  sessionsRestored: number;
  sessionsExpired: number;
  storageFailures: number;

  // Performance
  avgStateCaptureTime: number;
  avgStateRestoreTime: number;
  avgCheckpointTime: number;

  // User behavior
  recoveryBannerDismissals: number;
  startFreshClicks: number;
  retryClicks: number;
}
```

**Monitoring Dashboard:**
```
┌─────────────────────────────────────────────────────────────┐
│          Error Handling & Recovery Dashboard                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Error Rate:        2.3% (▼ 0.5% from last week)           │
│  Recovery Rate:     94.5% (▲ 2.1% from last week)          │
│  Avg Recovery Time: 8.2s                                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Errors by Category (Last 24h)                       │   │
│  │                                                       │   │
│  │  TRANSIENT:    █████████░░░░░░░  58% (142)          │   │
│  │  RECOVERABLE:  ███████░░░░░░░░░  35% (85)           │   │
│  │  PERMANENT:    ██░░░░░░░░░░░░░░   7% (18)           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Recovery Success Rate by Attempt                    │   │
│  │                                                       │   │
│  │  Auto Retry 1: ██████████████████  92%              │   │
│  │  Auto Retry 2: ███████████████░░░  78%              │   │
│  │  Auto Retry 3: ██████████░░░░░░░  65%               │   │
│  │  Manual Retry: ████████████████░░  84%              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Most Common Errors                                  │   │
│  │                                                       │   │
│  │  1. Network timeout (Agent 2)           45 occurrences│   │
│  │  2. LLM rate limit (Agent 4)            28 occurrences│   │
│  │  3. File processing error (Agent 3)     12 occurrences│   │
│  │  4. Database connection timeout          8 occurrences│   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Performance Metrics (p95)                           │   │
│  │                                                       │   │
│  │  State Capture:    245ms  ✓ Within target (500ms)   │   │
│  │  State Restore:    680ms  ✓ Within target (1s)      │   │
│  │  Checkpoint Save:   72ms  ✓ Within target (100ms)   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Alerts:**

```yaml
# alerts.yaml

# High error rate
- name: error_rate_high
  condition: error_rate > 5%
  duration: 5m
  severity: warning
  message: "Error rate {{error_rate}}% exceeds threshold"

# Low recovery rate
- name: recovery_rate_low
  condition: recovery_rate < 85%
  duration: 10m
  severity: critical
  message: "Recovery rate {{recovery_rate}}% below threshold"

# Storage failures
- name: storage_failures
  condition: storage_failure_rate > 1%
  duration: 5m
  severity: warning
  message: "Storage failures at {{storage_failure_rate}}%"

# Performance degradation
- name: state_capture_slow
  condition: avg_state_capture_time > 1000ms
  duration: 5m
  severity: warning
  message: "State capture slow: {{avg_state_capture_time}}ms"
```

### 11.3 Rollback Plan

**Triggers:**
- Error rate > 10%
- Recovery rate < 70%
- Performance degradation > 50%
- Critical bugs discovered

**Rollback Steps:**

1. **Immediate:**
   - Disable feature flag (set to 0%)
   - All users revert to old behavior
   - Monitor error rates normalize

2. **Investigation:**
   - Analyze metrics and logs
   - Identify root cause
   - Develop fix

3. **Re-deployment:**
   - Deploy fix to staging
   - Validate fix
   - Resume progressive rollout

**Feature Flag Configuration:**
```typescript
// Feature flag service
const FEATURE_FLAGS = {
  ERROR_HANDLING_ENABLED: {
    percentage: 100,  // 0-100
    enabledFor: [],   // Specific user IDs
    disabledFor: []   // Excluded user IDs
  }
};

function isErrorHandlingEnabled(userId?: string): boolean {
  const flag = FEATURE_FLAGS.ERROR_HANDLING_ENABLED;

  if (userId && flag.disabledFor.includes(userId)) {
    return false;
  }

  if (userId && flag.enabledFor.includes(userId)) {
    return true;
  }

  // Random sampling based on percentage
  return Math.random() * 100 < flag.percentage;
}
```

---

## 12. Success Criteria

### 12.1 Quantitative Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Zero data loss rate | 100% | No user should lose their data |
| Recovery success rate | > 90% | Most failures should be recoverable |
| Auto-retry success rate | > 80% | Transient errors should self-heal |
| State capture time (p95) | < 500ms | No noticeable UI delay |
| State restore time (p95) | < 1s | Fast return to input screen |
| Error classification accuracy | > 95% | Correct category for retry logic |
| User satisfaction (survey) | > 4.0/5 | Users find recovery helpful |

### 12.2 Qualitative Goals

- **User Experience:** Users feel confident their data is safe
- **Transparency:** Clear communication about what went wrong
- **Simplicity:** Recovery process is straightforward
- **Reliability:** System consistently preserves and restores state
- **Debuggability:** Engineering team can diagnose issues quickly

### 12.3 Acceptance Tests

Before marking the project complete, verify:

- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] Chaos tests pass consistently
- [ ] Performance targets met
- [ ] Security review complete
- [ ] Accessibility review complete
- [ ] Documentation complete
- [ ] Monitoring dashboard operational
- [ ] Alerts configured and tested
- [ ] Rollout plan approved
- [ ] Stakeholder demo successful

---

## Appendix A: User Flows

### Flow 1: Successful Recovery After Network Timeout

```
User Journey:
1. User uploads resume and enters job posting
2. Clicks "Optimize"
3. Sees processing screen with progress
4. Network connection lost during Agent 3
5. Error banner appears: "Connection lost"
6. Automatically retrying in 2 seconds...
7. Retry succeeds
8. Processing continues from Agent 3
9. User sees final optimized resume
10. No data loss, minimal disruption

User Impact: Positive - system recovered automatically
```

### Flow 2: Manual Recovery After LLM Failure

```
User Journey:
1. User uploads resume and enters job posting
2. Clicks "Optimize"
3. Sees processing screen
4. LLM API fails during Agent 4 (rate limit)
5. Redirected to input screen
6. Recovery banner shows: "Service temporarily unavailable.
   Your data from 2 minutes ago has been preserved."
7. User clicks "Retry Processing"
8. System uses fallback model
9. Processing completes successfully
10. User sees optimized resume

User Impact: Neutral - required manual action but no data loss
```

### Flow 3: Recovery After Browser Crash

```
User Journey:
1. User uploads large resume (8MB) and enters long job posting
2. Clicks "Optimize"
3. Sees processing screen
4. Browser crashes unexpectedly
5. User reopens browser and navigates back to site
6. Recovery banner appears: "You have unsaved work from 5 minutes ago"
7. Form is pre-filled, file name shown
8. User clicks "Retry Processing"
9. Processing completes from last checkpoint
10. User sees optimized resume

User Impact: Very Positive - expected to lose everything,
             but system preserved all data
```

---

## Appendix B: Error Message Templates

### Transient Errors

**Network Timeout:**
```
Title: Connection Timeout
Message: The network connection timed out while processing your request.
         This is usually temporary.
Action: Retrying automatically in {countdown} seconds...
Support: If this persists, check your internet connection.
```

**Rate Limiting:**
```
Title: Service Busy
Message: The AI service is currently experiencing high demand.
         Your data has been preserved.
Action: Retrying automatically in {countdown} seconds...
Support: This should resolve itself shortly.
```

### Recoverable Errors

**LLM Processing Error:**
```
Title: Processing Error
Message: An error occurred while analyzing your resume.
         Your data has been saved.
Action: Click "Retry Processing" to try again with an alternative model.
Support: If this continues, try simplifying your job posting or resume.
```

**File Processing Error:**
```
Title: File Processing Issue
Message: We had trouble reading your resume file. Your upload has been preserved.
Action: Click "Retry Processing" to try again, or upload a different file format.
Support: Supported formats: PDF, DOCX. Try converting your file if issues persist.
```

### Permanent Errors

**Invalid File Type:**
```
Title: Unsupported File Type
Message: The uploaded file type is not supported.
         Please upload a PDF or DOCX file.
Action: Click "Start Fresh" and upload a supported file.
Support: Supported formats: PDF (.pdf), Word (.docx, .doc)
```

**Authentication Error:**
```
Title: Service Configuration Error
Message: There's a configuration issue preventing processing.
         This is not your fault.
Action: Please try again later or contact support.
Support: Reference ID: {error_id}
        Email: support@example.com
```

---

## Appendix C: Database Schema Reference

Full SQL schema for all new tables:

```sql
-- Recovery sessions table
CREATE TABLE recovery_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    application_id INTEGER,

    -- User input state
    form_data TEXT NOT NULL,  -- JSON
    file_metadata TEXT,       -- JSON

    -- Processing state
    status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'failed', 'recovered')),
    current_agent INTEGER CHECK(current_agent >= 0 AND current_agent <= 4),
    completed_agents TEXT,    -- JSON array

    -- Error context
    error_id TEXT,
    error_type TEXT,
    error_category TEXT CHECK(error_category IN ('TRANSIENT', 'RECOVERABLE', 'PERMANENT')),
    error_message TEXT,
    error_stacktrace TEXT,

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP,

    -- Request context
    ip_address TEXT,
    user_agent TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,

    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE INDEX idx_recovery_session_id ON recovery_sessions(session_id);
CREATE INDEX idx_recovery_status ON recovery_sessions(status, expires_at);
CREATE INDEX idx_recovery_expires ON recovery_sessions(expires_at);
CREATE INDEX idx_recovery_application ON recovery_sessions(application_id);

-- Agent checkpoints table
CREATE TABLE agent_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_index INTEGER NOT NULL CHECK(agent_index >= 0 AND agent_index <= 4),
    agent_name TEXT NOT NULL,

    -- Agent output
    agent_output TEXT NOT NULL,  -- JSON

    -- Execution metadata
    execution_time_ms INTEGER,
    model_used TEXT,
    tokens_used INTEGER,
    cost_usd REAL,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES recovery_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_checkpoint_session ON agent_checkpoints(session_id);
CREATE INDEX idx_checkpoint_agent ON agent_checkpoints(session_id, agent_index);
CREATE UNIQUE INDEX idx_checkpoint_unique ON agent_checkpoints(session_id, agent_index);

-- Error logs table
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_id TEXT UNIQUE NOT NULL,
    session_id TEXT,

    -- Error details
    error_type TEXT NOT NULL,
    error_category TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_stacktrace TEXT,

    -- Request context
    request_path TEXT,
    request_method TEXT,
    user_agent TEXT,
    ip_address TEXT,

    -- Additional context
    additional_context TEXT,  -- JSON

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES recovery_sessions(session_id) ON DELETE SET NULL
);

CREATE INDEX idx_error_id ON error_logs(error_id);
CREATE INDEX idx_error_session ON error_logs(session_id);
CREATE INDEX idx_error_created ON error_logs(created_at DESC);
CREATE INDEX idx_error_category ON error_logs(error_category, created_at DESC);

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_recovery_sessions_timestamp
AFTER UPDATE ON recovery_sessions
BEGIN
    UPDATE recovery_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

---

## Appendix D: API Endpoints

### POST /api/optimize-retry

Resume processing from preserved state.

**Request:**
```typescript
{
  sessionId: string;         // Recovery session ID
  formData?: {               // Optional - override preserved data
    jobPosting: string;
    isJobUrl: boolean;
    additionalNotes?: string;
  };
  checkpointId?: string;     // Optional - specific checkpoint
}
```

**Response (Success):**
```typescript
{
  success: true;
  applicationId: number;
  resumedFromAgent: number;  // Which agent pipeline resumed from
  sessionId: string;
}
```

**Response (Error):**
```typescript
{
  success: false;
  error: string;
  errorId: string;
  category: 'TRANSIENT' | 'RECOVERABLE' | 'PERMANENT';
  retryable: boolean;
  recovery_metadata: {
    sessionId: string;
    checkpointAvailable: boolean;
  };
}
```

### GET /api/recovery-session/:sessionId

Retrieve recovery session details.

**Response:**
```typescript
{
  success: true;
  session: {
    sessionId: string;
    status: string;
    formData: any;
    fileMetadata: any;
    errorContext: {
      errorId: string;
      errorType: string;
      errorMessage: string;
      category: string;
    };
    completedAgents: number[];
    retryCount: number;
    createdAt: string;
    expiresAt: string;
  };
}
```

### DELETE /api/recovery-session/:sessionId

Delete recovery session (user clicked "Start Fresh").

**Response:**
```typescript
{
  success: true;
  message: "Recovery session deleted";
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-31 | System Architecture | Initial specification |

---

## References

- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
