/**
 * Persist and restore conversation state across full-page navigations
 * (e.g. OAuth redirect → Google → /auth/callback → /).
 *
 * JSON-safe fields (messages, data metadata, phase, stepId) live in
 * **sessionStorage**.  File blobs (`File` objects) can't be serialised to
 * JSON, so they're stashed in **IndexedDB** and re-attached on restore.
 *
 * Both stores are one-shot: `loadSnapshot` clears them immediately after
 * reading so stale state never leaks into a future session.
 */

import type { ConversationState, CollectedData, Message, Phase } from './types';

// ── Keys / Names ──────────────────────────────────────────────────────
const STORAGE_KEY = 'resume-optimizer:conversation-snapshot';
const IDB_NAME = 'resume-optimizer-files';
const IDB_STORE = 'blobs';
const IDB_VERSION = 1;

// ── Public snapshot shape ─────────────────────────────────────────────
export interface ConversationSnapshot {
  messages: Message[];
  data: CollectedData;
  currentStepId: string | undefined;
  phase: Phase;
  /** True when File blobs were stashed in IndexedDB. */
  hasFiles: boolean;
}

// ── IndexedDB helpers (thin, promise-based) ───────────────────────────

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, IDB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(IDB_STORE)) {
        db.createObjectStore(IDB_STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbPut(key: string, value: File): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readwrite');
    tx.objectStore(IDB_STORE).put(value, key);
    tx.oncomplete = () => { db.close(); resolve(); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

async function idbGet(key: string): Promise<File | undefined> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readonly');
    const req = tx.objectStore(IDB_STORE).get(key);
    req.onsuccess = () => { db.close(); resolve(req.result as File | undefined); };
    req.onerror = () => { db.close(); reject(req.error); };
  });
}

async function idbClear(): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readwrite');
    tx.objectStore(IDB_STORE).clear();
    tx.oncomplete = () => { db.close(); resolve(); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

// ── Save ──────────────────────────────────────────────────────────────

/**
 * Snapshot the current conversation state so it survives a full-page
 * redirect. Call this **synchronously before** the OAuth redirect fires.
 *
 * File blobs are persisted to IndexedDB (async but fire-and-forget; the
 * browser will flush before navigating away in practice).
 */
export function saveSnapshot(state: ConversationState): void {
  // Strip non-serialisable `File` objects from data; keep metadata.
  const cleanData: CollectedData = { ...state.data };
  let hasFiles = false;

  if (cleanData.resumeFile?.file) {
    const file = cleanData.resumeFile.file;
    cleanData.resumeFile = {
      name: cleanData.resumeFile.name,
      size: cleanData.resumeFile.size,
      mime: cleanData.resumeFile.mime,
    };
    hasFiles = true;
    // Fire-and-forget — browser will flush IDB before navigating away.
    void idbPut('resumeFile', file);
  }

  if (cleanData.additionalProfileFile?.file) {
    const file = cleanData.additionalProfileFile.file;
    cleanData.additionalProfileFile = {
      name: cleanData.additionalProfileFile.name,
      size: cleanData.additionalProfileFile.size,
      mime: cleanData.additionalProfileFile.mime,
    };
    hasFiles = true;
    void idbPut('additionalProfileFile', file);
  }

  const snapshot: ConversationSnapshot = {
    messages: state.messages,
    data: cleanData,
    currentStepId: state.currentStepId,
    phase: state.phase,
    hasFiles,
  };

  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch (err) {
    console.warn('[sessionPersistence] Failed to save snapshot:', err);
  }
}

// ── Load ──────────────────────────────────────────────────────────────

/**
 * Attempt to restore a previously-saved snapshot. Returns `null` when
 * nothing is stored. **Always** clears the stored snapshot (one-shot).
 *
 * File blobs are re-attached from IndexedDB when `hasFiles` is set.
 */
export async function loadSnapshot(): Promise<ConversationSnapshot | null> {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  // Always clear — whether we succeed or not, the snapshot is consumed.
  sessionStorage.removeItem(STORAGE_KEY);

  if (!raw) return null;

  let snapshot: ConversationSnapshot;
  try {
    snapshot = JSON.parse(raw) as ConversationSnapshot;
  } catch {
    return null;
  }

  // Re-attach File blobs from IndexedDB.
  if (snapshot.hasFiles) {
    try {
      const resumeBlob = await idbGet('resumeFile');
      if (resumeBlob && snapshot.data.resumeFile) {
        snapshot.data.resumeFile = {
          ...snapshot.data.resumeFile,
          file: resumeBlob,
        };
      }

      const additionalBlob = await idbGet('additionalProfileFile');
      if (additionalBlob && snapshot.data.additionalProfileFile) {
        snapshot.data.additionalProfileFile = {
          ...snapshot.data.additionalProfileFile,
          file: additionalBlob,
        };
      }
    } catch (err) {
      console.warn('[sessionPersistence] IndexedDB file restore failed:', err);
      // Non-fatal — metadata is still available so the context strip
      // will show the filename, and ProcessingStream can re-prompt.
    } finally {
      void idbClear();
    }
  }

  return snapshot;
}
