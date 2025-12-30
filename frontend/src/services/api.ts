import type { ResumeChange } from '../types';
import { supabase } from '../lib/supabase';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class UsageLimitError extends Error {
  remaining: number;
  
  constructor(message: string, remaining: number) {
    super(message);
    this.name = 'UsageLimitError';
    this.remaining = remaining;
  }
}

export interface JobAnalysisResponse {
  success: boolean;
  application_id: number;
  company_name: string;
  job_title: string;
  analysis: string;
  job_text: string;
}

export interface OptimizationResponse {
  success: boolean;
  application_id: number;
  strategy: string;
}

export interface ImplementationResponse {
  success: boolean;
  application_id: number;
  optimized_resume: string;
  notes: string;
}

export interface ValidationResponse {
  success: boolean;
  application_id: number;
  validation: string;
  scores: {
    overall: number;
    requirements_match: number;
    ats_optimization: number;
    cultural_fit: number;
  };
}

export interface PolishResponse {
  success: boolean;
  application_id: number;
  final_resume: string;
  notes: string;
}

export interface UploadResumeResponse {
  success: boolean;
  filename: string;
  text: string;
  length: number;
}

export interface JobPreviewResponse {
  success: boolean;
  job_text: string;
  decision: string;
  reasons: string[];
}

export interface ProfileStatusResponse {
  success: boolean;
  linkedin: {
    connected: boolean;
    cached_at: string | null;
    profile_id: number | null;
  };
  github: {
    connected: boolean;
    cached_at: string | null;
    profile_id: number | null;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async buildAuthHeaders(): Promise<Record<string, string>> {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.access_token) {
      return { 'Authorization': `Bearer ${session.access_token}` };
    }
    
    return {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const authHeaders = await this.buildAuthHeaders();
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        
        // Handle 402 Payment Required (usage limit reached)
        if (response.status === 402) {
          throw new UsageLimitError(error.detail || 'Usage limit reached', error.remaining ?? 0);
        }
        
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async uploadResume(file: File): Promise<UploadResumeResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const authHeaders = await this.buildAuthHeaders();

    const response = await fetch(`${this.baseUrl}/api/upload-resume`, {
      method: 'POST',
      body: formData,
      headers: authHeaders,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async analyzeJob(params: {
    job_text?: string;
    job_url?: string;
  }): Promise<JobAnalysisResponse> {
    return this.request<JobAnalysisResponse>('/api/analyze-job', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async jobPreview(job_url: string): Promise<JobPreviewResponse> {
    return this.request<JobPreviewResponse>('/api/job-preview', {
      method: 'POST',
      body: JSON.stringify({ job_url }),
    });
  }

  async optimizeResume(params: {
    application_id: number;
    resume_text: string;
    github_username?: string;
  }): Promise<OptimizationResponse> {
    return this.request<OptimizationResponse>('/api/optimize-resume', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async implementOptimization(application_id: number): Promise<ImplementationResponse> {
    return this.request<ImplementationResponse>('/api/implement', {
      method: 'POST',
      body: JSON.stringify({ application_id }),
    });
  }

  async validateResume(application_id: number): Promise<ValidationResponse> {
    return this.request<ValidationResponse>('/api/validate', {
      method: 'POST',
      body: JSON.stringify({ application_id }),
    });
  }

  async polishResume(params: {
    application_id: number;
    output_format?: string;
  }): Promise<PolishResponse> {
    return this.request<PolishResponse>('/api/polish', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async exportResume(application_id: number, format: string = 'docx'): Promise<Blob> {
    const authHeaders = await this.buildAuthHeaders();
    const response = await fetch(
      `${this.baseUrl}/api/export/${application_id}?format=${format}`,
      {
        headers: authHeaders,
      }
    );

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return await response.blob();
  }

  getExportUrl(application_id: number, format: string = 'docx'): string {
    return `${this.baseUrl}/api/export/${application_id}?format=${format}`;
  }

  async getApplication(application_id: number): Promise<any> {
    return this.request(`/api/application/${application_id}`, {
      method: 'GET',
    });
  }

  async getApplicationDiff(application_id: number): Promise<{
    success: boolean;
    changes: ResumeChange[];
    scores: {
      overall: number;
      requirements_match: number;
      ats_optimization: number;
      cultural_fit: number;
    };
  }> {
    return this.request(`/api/application/${application_id}/diff`, {
      method: 'GET',
    });
  }

  async listApplications(): Promise<any> {
    return this.request('/api/applications', {
      method: 'GET',
    });
  }

  async startPipeline(params: {
    resume_text: string;
    job_text?: string;
    job_url?: string;
    linkedin_url?: string;
    github_username?: string;
    github_token?: string;
    force_refresh_profile?: boolean;
  }): Promise<{ success: boolean; job_id: string; stream_url: string; snapshot_url: string }> {
    return this.request('/api/pipeline/start', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async getProfileStatus(params: {
    linkedin_url?: string;
    github_username?: string;
  }): Promise<ProfileStatusResponse> {
    return this.request('/api/profile/status', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async getJobSnapshot(job_id: string): Promise<any> {
    return this.request(`/api/jobs/${job_id}/snapshot`, {
      method: 'GET',
    });
  }

  getStreamUrl(job_id: string): string {
    return `${this.baseUrl}/api/jobs/${job_id}/stream`;
  }
}

export const apiClient = new ApiClient();
