-- Migration: Add error recovery and state preservation tables
-- Version: 002
-- Date: 2025-10-31

-- Recovery sessions table
CREATE TABLE IF NOT EXISTS recovery_sessions (
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

CREATE INDEX IF NOT EXISTS idx_recovery_session_id ON recovery_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_recovery_status ON recovery_sessions(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_recovery_expires ON recovery_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_recovery_application ON recovery_sessions(application_id);

-- Agent checkpoints table
CREATE TABLE IF NOT EXISTS agent_checkpoints (
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

CREATE INDEX IF NOT EXISTS idx_checkpoint_session ON agent_checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_agent ON agent_checkpoints(session_id, agent_index);
CREATE UNIQUE INDEX IF NOT EXISTS idx_checkpoint_unique ON agent_checkpoints(session_id, agent_index);

-- Error logs table
CREATE TABLE IF NOT EXISTS error_logs (
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

CREATE INDEX IF NOT EXISTS idx_error_id ON error_logs(error_id);
CREATE INDEX IF NOT EXISTS idx_error_session ON error_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_error_created ON error_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_category ON error_logs(error_category, created_at DESC);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_recovery_sessions_timestamp
AFTER UPDATE ON recovery_sessions
BEGIN
    UPDATE recovery_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
