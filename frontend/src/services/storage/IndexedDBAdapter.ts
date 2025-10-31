/**
 * IndexedDB adapter for file storage
 */

export interface FileStore {
  key: string;
  sessionId: string;
  blob: Blob;
  fileName: string;
  fileType: string;
  fileSize: number;
  uploadedAt: number;
  hash: string;
}

export class IndexedDBAdapter {
  private dbName = 'ResumeOptimizerDB';
  private version = 1;
  private db: IDBDatabase | null = null;

  /**
   * Initialize IndexedDB
   */
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
      };
    });
  }

  /**
   * Save file to IndexedDB
   */
  async saveFile(sessionId: string, file: File): Promise<string> {
    if (!this.db) await this.init();

    const fileKey = this.generateFileKey();
    const hash = await this.calculateHash(file);

    const fileRecord: FileStore = {
      key: fileKey,
      sessionId,
      blob: file,
      fileName: file.name,
      fileType: file.type,
      fileSize: file.size,
      uploadedAt: Date.now(),
      hash,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['files'], 'readwrite');
      const store = transaction.objectStore('files');
      const request = store.add(fileRecord);

      request.onsuccess = () => resolve(fileKey);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Load file from IndexedDB
   */
  async loadFile(fileKey: string): Promise<File | null> {
    if (!this.db) await this.init();

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
          lastModified: record.uploadedAt,
        });

        resolve(file);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Verify file integrity
   */
  async verifyFile(fileKey: string): Promise<boolean> {
    const file = await this.loadFile(fileKey);
    if (!file) return false;

    const transaction = this.db!.transaction(['files'], 'readonly');
    const store = transaction.objectStore('files');

    return new Promise((resolve, reject) => {
      const request = store.get(fileKey);

      request.onsuccess = async () => {
        const record = request.result as FileStore | undefined;
        if (!record) {
          resolve(false);
          return;
        }

        // Verify hash
        const currentHash = await this.calculateHash(file);
        resolve(currentHash === record.hash);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Delete file from IndexedDB
   */
  async deleteFile(fileKey: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['files'], 'readwrite');
      const store = transaction.objectStore('files');
      const request = store.delete(fileKey);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Cleanup session files
   */
  async cleanupSession(sessionId: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['files'], 'readwrite');
      const store = transaction.objectStore('files');
      const index = store.index('sessionId');

      const request = index.openCursor(IDBKeyRange.only(sessionId));

      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all files for session
   */
  async getSessionFiles(sessionId: string): Promise<FileStore[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['files'], 'readonly');
      const store = transaction.objectStore('files');
      const index = store.index('sessionId');

      const request = index.getAll(sessionId);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Calculate file hash (SHA-256)
   */
  private async calculateHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Generate unique file key
   */
  private generateFileKey(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Check if IndexedDB is available
   */
  static isAvailable(): boolean {
    return typeof indexedDB !== 'undefined';
  }

  /**
   * Close database connection
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }
}

export default IndexedDBAdapter;
