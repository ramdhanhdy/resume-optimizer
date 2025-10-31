/**
 * State Manager for recovery session coordination
 */

import LocalStorageAdapter, { RecoverySession } from './LocalStorageAdapter';
import IndexedDBAdapter from './IndexedDBAdapter';

export interface CaptureStateOptions {
  formData: {
    jobPosting: string;
    isJobUrl: boolean;
    additionalNotes?: string;
  };
  file?: File | null;
  errorContext?: {
    errorId: string;
    errorType: string;
    errorMessage: string;
    category: 'TRANSIENT' | 'RECOVERABLE' | 'PERMANENT';
  };
  reason: string;
}

export class StateManager {
  private static instance: StateManager | null = null;
  private localStorageAdapter: LocalStorageAdapter;
  private indexedDBAdapter: IndexedDBAdapter;
  private initialized = false;

  private constructor() {
    this.localStorageAdapter = new LocalStorageAdapter();
    this.indexedDBAdapter = new IndexedDBAdapter();
  }

  /**
   * Get singleton instance
   */
  static getInstance(): StateManager {
    if (!StateManager.instance) {
      StateManager.instance = new StateManager();
    }
    return StateManager.instance;
  }

  /**
   * Initialize storage adapters
   */
  async init(): Promise<void> {
    if (this.initialized) return;

    if (IndexedDBAdapter.isAvailable()) {
      await this.indexedDBAdapter.init();
    }

    this.initialized = true;
  }

  /**
   * Capture current state
   */
  async captureState(options: CaptureStateOptions): Promise<string> {
    await this.init();

    const sessionId = this.generateSessionId();
    const now = Date.now();
    const expiresAt = now + (7 * 24 * 60 * 60 * 1000); // 7 days

    // Handle file storage
    let fileMetadata: RecoverySession['fileMetadata'] = null;
    if (options.file) {
      try {
        const fileKey = await this.indexedDBAdapter.saveFile(sessionId, options.file);
        const hash = await this.calculateFileHash(options.file);

        fileMetadata = {
          fileName: options.file.name,
          fileSize: options.file.size,
          fileType: options.file.type,
          indexedDBKey: fileKey,
          uploadedAt: now,
          fileHash: hash,
        };
      } catch (e) {
        console.error('Failed to save file to IndexedDB:', e);
      }
    }

    // Build recovery session
    const session: RecoverySession = {
      sessionId,
      version: '1.0',
      createdAt: now,
      expiresAt,
      formData: options.formData,
      fileMetadata,
      processingState: {
        status: 'failed',
        currentAgent: null,
        completedAgents: [],
        lastCheckpointId: null,
      },
      errorContext: options.errorContext
        ? {
            ...options.errorContext,
            occurredAt: now,
            retryCount: 0,
            lastRetryAt: null,
          }
        : null,
      recovery: {
        canAutoRetry: options.errorContext?.category === 'TRANSIENT',
        canManualRetry: options.errorContext?.category !== 'PERMANENT',
        suggestedAction: this.getSuggestedAction(options.errorContext),
        supportReferenceId: options.errorContext?.errorId || sessionId,
      },
    };

    // Save to LocalStorage
    this.localStorageAdapter.saveSession(session);

    return sessionId;
  }

  /**
   * Restore state from session
   */
  async restoreState(sessionId: string): Promise<RecoverySession | null> {
    await this.init();

    const session = this.localStorageAdapter.loadSession(sessionId);
    if (!session) return null;

    // Verify file integrity if present
    if (session.fileMetadata) {
      try {
        const isValid = await this.indexedDBAdapter.verifyFile(
          session.fileMetadata.indexedDBKey
        );
        if (!isValid) {
          console.warn('File integrity check failed');
        }
      } catch (e) {
        console.error('Failed to verify file:', e);
      }
    }

    return session;
  }

  /**
   * Load file from session
   */
  async loadFile(sessionId: string): Promise<File | null> {
    await this.init();

    const session = this.localStorageAdapter.loadSession(sessionId);
    if (!session?.fileMetadata) return null;

    try {
      return await this.indexedDBAdapter.loadFile(session.fileMetadata.indexedDBKey);
    } catch (e) {
      console.error('Failed to load file:', e);
      return null;
    }
  }

  /**
   * Find latest session
   */
  async findLatestSession(): Promise<RecoverySession | null> {
    await this.init();
    return this.localStorageAdapter.findLatestSession();
  }

  /**
   * Update session
   */
  async updateSession(sessionId: string, updates: Partial<RecoverySession>): Promise<void> {
    const session = this.localStorageAdapter.loadSession(sessionId);
    if (!session) throw new Error('Session not found');

    const updated: RecoverySession = { ...session, ...updates };
    this.localStorageAdapter.saveSession(updated);
  }

  /**
   * Increment retry count
   */
  async incrementRetryCount(sessionId: string): Promise<number> {
    const session = this.localStorageAdapter.loadSession(sessionId);
    if (!session) throw new Error('Session not found');

    const newCount = (session.errorContext?.retryCount || 0) + 1;

    if (session.errorContext) {
      session.errorContext.retryCount = newCount;
      session.errorContext.lastRetryAt = Date.now();
    }

    this.localStorageAdapter.saveSession(session);
    return newCount;
  }

  /**
   * Cleanup session
   */
  async cleanupSession(sessionId: string): Promise<void> {
    await this.init();

    // Delete from LocalStorage
    this.localStorageAdapter.deleteSession(sessionId);

    // Delete files from IndexedDB
    try {
      await this.indexedDBAdapter.cleanupSession(sessionId);
    } catch (e) {
      console.error('Failed to cleanup IndexedDB:', e);
    }
  }

  /**
   * Cleanup all expired sessions
   */
  async cleanupExpiredSessions(): Promise<void> {
    await this.init();
    this.localStorageAdapter.cleanupOldSessions();
  }

  /**
   * Get suggested action based on error
   */
  private getSuggestedAction(
    errorContext?: { category: 'TRANSIENT' | 'RECOVERABLE' | 'PERMANENT' }
  ): string {
    if (!errorContext) {
      return 'Click "Retry Processing" to try again.';
    }

    switch (errorContext.category) {
      case 'TRANSIENT':
        return 'Retrying automatically. You can also click "Retry Processing" to try immediately.';
      case 'RECOVERABLE':
        return 'Click "Retry Processing" to try again, or "Start Fresh" to begin a new session.';
      case 'PERMANENT':
        return 'Please fix the issue and click "Start Fresh" to begin a new session.';
      default:
        return 'Click "Retry Processing" to try again.';
    }
  }

  /**
   * Generate session ID
   */
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Calculate file hash
   */
  private async calculateFileHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}

// Export singleton instance
export default StateManager.getInstance();
