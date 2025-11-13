const STORAGE_KEY = 'resume-optimizer-client-id';

function generateId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getClientId(): string | null {
  if (typeof window === 'undefined' || !window.localStorage) {
    return null;
  }

  try {
    const existing = window.localStorage.getItem(STORAGE_KEY);
    if (existing) {
      return existing;
    }

    const nextId = generateId();
    window.localStorage.setItem(STORAGE_KEY, nextId);
    return nextId;
  } catch (error) {
    console.warn('Unable to access localStorage for client ID:', error);
    return null;
  }
}

