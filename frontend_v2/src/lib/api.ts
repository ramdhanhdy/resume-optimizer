import { supabase } from './supabase';
import type { ApplicationReview } from '@/types/review';

// Empty string = same-origin (dev uses Vite's /api proxy). Only fall back
// to the explicit localhost default when the env var is genuinely missing.
const rawApiUrl = import.meta.env.VITE_API_URL as string | undefined;
export const API_BASE_URL =
  rawApiUrl === undefined ? 'http://localhost:8000' : rawApiUrl;

export const MOCK_STREAM =
  (import.meta.env.VITE_MOCK_STREAM as string | undefined) === 'true';

const DEV_BYPASS_ENABLED =
  (import.meta.env.VITE_AUTH_BYPASS as string | undefined) === 'true';

function getDevClientId(): string {
  if (typeof window === 'undefined') return 'frontend-v2-dev';
  const storageKey = 'resume-optimizer:frontend-v2:client-id';
  const existing = window.localStorage.getItem(storageKey);
  if (existing) return existing;

  const generated =
    typeof window.crypto?.randomUUID === 'function'
      ? window.crypto.randomUUID()
      : `frontend-v2-${Date.now().toString(36)}`;
  window.localStorage.setItem(storageKey, generated);
  return generated;
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  if (!supabase) {
    return DEV_BYPASS_ENABLED ? { 'X-Client-Id': getDevClientId() } : {};
  }
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (session?.access_token) {
    return { Authorization: `Bearer ${session.access_token}` };
  }
  return DEV_BYPASS_ENABLED ? { 'X-Client-Id': getDevClientId() } : {};
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(await getAuthHeaders()),
    ...((options.headers as Record<string, string>) ?? {}),
  };
  const res = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* swallow */
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

/** POST /api/upload-resume — returns extracted text from a PDF/DOCX file. */
export async function uploadResume(file: File): Promise<{ text: string; filename: string }> {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch(`${API_BASE_URL}/api/upload-resume`, {
    method: 'POST',
    body: fd,
    headers: await getAuthHeaders(),
  });
  if (!res.ok) throw new ApiError(`Upload failed: ${res.statusText}`, res.status);
  return res.json();
}

export interface StartPipelineInput {
  resume_text: string;
  job_text?: string;
  job_url?: string;
  resume_filename?: string;
}

export interface StartPipelineResponse {
  success: boolean;
  job_id: string;
  stream_url: string;
  snapshot_url: string;
}

export interface ApplicationReviewResponse {
  success: boolean;
  review: ApplicationReview;
}

/** POST /api/pipeline/start — kicks off the streaming optimization job. */
export async function startPipeline(
  input: StartPipelineInput,
): Promise<StartPipelineResponse> {
  return request<StartPipelineResponse>('/api/pipeline/start', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function getApplicationReview(
  applicationId: number,
): Promise<ApplicationReview> {
  const response = await request<ApplicationReviewResponse>(
    `/api/applications/${applicationId}/review`,
    { method: 'GET' },
  );
  return response.review;
}

export interface RefineResumeInput {
  applicationId: number;
  instruction: string;
  current: ApplicationReview;
}

export async function refineResume(
  input: RefineResumeInput,
): Promise<ApplicationReview> {
  const response = await request<ApplicationReviewResponse>(
    `/api/applications/${input.applicationId}/refine`,
    {
      method: 'POST',
      body: JSON.stringify({ instruction: input.instruction }),
    },
  );
  return response.review;
}

export async function fetchAuthenticatedBlob(
  endpointOrUrl: string,
): Promise<{ blob: Blob; filename?: string }> {
  const url = endpointOrUrl.startsWith('http')
    ? endpointOrUrl
    : `${API_BASE_URL}${endpointOrUrl}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: await getAuthHeaders(),
  });
  if (!res.ok) {
    throw new ApiError(`Download failed: ${res.statusText}`, res.status);
  }

  const disposition = res.headers.get('content-disposition') ?? '';
  let filename: string | undefined;
  const filenameStarMatch = disposition.match(/filename\*\s*=\s*([^;]+)/i);
  if (filenameStarMatch) {
    const rawValue = filenameStarMatch[1].trim().replace(/^"(.*)"$/, '$1');
    const encodedValue = rawValue.replace(/^[^']*'[^']*'/, '');
    try {
      filename = decodeURIComponent(encodedValue);
    } catch {
      filename = undefined;
    }
  }
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);
  if (!filename) {
    filename = filenameMatch?.[1];
  }

  return {
    blob: await res.blob(),
    filename,
  };
}
