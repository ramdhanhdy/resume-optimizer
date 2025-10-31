/**
 * Storage services for state preservation
 */

export { LocalStorageAdapter } from './LocalStorageAdapter';
export { IndexedDBAdapter } from './IndexedDBAdapter';
export { StateManager } from './StateManager';
export type { RecoverySession } from './LocalStorageAdapter';
export type { FileStore } from './IndexedDBAdapter';
export type { CaptureStateOptions } from './StateManager';

// Export default StateManager instance
export { default as stateManager } from './StateManager';
