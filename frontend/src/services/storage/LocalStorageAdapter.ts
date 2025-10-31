/**
 * LocalStorage adapter for recovery session persistence
 */

export interface RecoverySession {
  // Metadata
  sessionId: string;
  version: string;
  createdAt: number;
  expiresAt: number;

  // User Input State
  formData: {
    jobPosting: string;
    isJobUrl: boolean;
    additionalNotes?: string;
  };

  // File State
  fileMetadata: {
    fileName: string;
    fileSize: number;
    fileType: string;
    indexedDBKey: string;
    uploadedAt: number;
    fileHash: string;
  } | null;

  // Processing State
  processingState: {
    status: 'pending' | 'processing' | 'failed';
    currentAgent: number | null;
    completedAgents: number[];
    lastCheckpointId: string | null;
  };

  // Error Context
  errorContext: {
    errorId: string;
    errorType: string;
    errorMessage: string;
    category: 'TRANSIENT' | 'RECOVERABLE' | 'PERMANENT';
    occurredAt: number;
    retryCount: number;
    lastRetryAt: number | null;
  } | null;

  // Recovery Metadata
  recovery: {
    canAutoRetry: boolean;
    canManualRetry: boolean;
    suggestedAction: string;
    supportReferenceId: string;
  };
}

export class LocalStorageAdapter {
  private readonly prefix = 'resume_optimizer_';
  private readonly schemaVersion = '1.0';

  /**
   * Save recovery session to LocalStorage
   */
  saveSession(session: RecoverySession): void {
    try {
      const key = `${this.prefix}recovery_${session.sessionId}`;
      const serialized = JSON.stringify(session);

      // Check size (limit to 1MB for safety)
      if (serialized.length > 1024 * 1024) {
        throw new Error('Session data too large for LocalStorage');
      }

      localStorage.setItem(key, serialized);
    } catch (e: any) {
      if (e.name === 'QuotaExceededError') {
        // Cleanup old sessions and retry
        this.cleanupOldSessions();
        const key = `${this.prefix}recovery_${session.sessionId}`;
        const serialized = JSON.stringify(session);
        localStorage.setItem(key, serialized);
      } else {
        throw e;
      }
    }
  }

  /**
   * Load recovery session from LocalStorage
   */
  loadSession(sessionId: string): RecoverySession | null {
    const key = `${this.prefix}recovery_${sessionId}`;
    const data = localStorage.getItem(key);

    if (!data) return null;

    try {
      const session = JSON.parse(data) as RecoverySession;

      // Check expiration
      if (Date.now() > session.expiresAt) {
        this.deleteSession(sessionId);
        return null;
      }

      return session;
    } catch (e) {
      console.error('Failed to parse recovery session:', e);
      return null;
    }
  }

  /**
   * Find latest non-expired session
   */
  findLatestSession(): RecoverySession | null {
    const sessions: RecoverySession[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(`${this.prefix}recovery_`)) continue;

      const data = localStorage.getItem(key);
      if (!data) continue;

      try {
        const session = JSON.parse(data) as RecoverySession;

        // Skip expired
        if (Date.now() > session.expiresAt) {
          localStorage.removeItem(key);
          continue;
        }

        sessions.push(session);
      } catch (e) {
        console.error('Failed to parse session:', e);
      }
    }

    if (sessions.length === 0) return null;

    // Return most recent
    return sessions.reduce((latest, current) =>
      current.createdAt > latest.createdAt ? current : latest
    );
  }

  /**
   * Delete recovery session
   */
  deleteSession(sessionId: string): void {
    const key = `${this.prefix}recovery_${sessionId}`;
    localStorage.removeItem(key);
  }

  /**
   * Cleanup old/expired sessions
   */
  cleanupOldSessions(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(`${this.prefix}recovery_`)) continue;

      const data = localStorage.getItem(key);
      if (!data) continue;

      try {
        const session = JSON.parse(data) as RecoverySession;
        if (now > session.expiresAt) {
          keysToDelete.push(key);
        }
      } catch (e) {
        // Invalid data, delete it
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => localStorage.removeItem(key));
  }

  /**
   * Get all active sessions
   */
  getAllSessions(): RecoverySession[] {
    const sessions: RecoverySession[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(`${this.prefix}recovery_`)) continue;

      const data = localStorage.getItem(key);
      if (!data) continue;

      try {
        const session = JSON.parse(data) as RecoverySession;

        // Skip expired
        if (Date.now() > session.expiresAt) {
          localStorage.removeItem(key);
          continue;
        }

        sessions.push(session);
      } catch (e) {
        console.error('Failed to parse session:', e);
      }
    }

    return sessions.sort((a, b) => b.createdAt - a.createdAt);
  }

  /**
   * Check if LocalStorage is available
   */
  isAvailable(): boolean {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (e) {
      return false;
    }
  }
}

export default LocalStorageAdapter;
