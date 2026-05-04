export interface UserPreferences {
  default_linkedin_url: string | null;
  default_github_username: string | null;
  default_resume_id: number | null;
  default_resume: {
    id: number;
    label: string | null;
    filename: string | null;
  } | null;
}

export interface UserPreferencesResponse {
  success: boolean;
  preferences: UserPreferences | null;
}

export interface SavedResume {
  id: number;
  label: string;
  filename: string | null;
  content_hash: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface SavedResumeDetail extends SavedResume {
  resume_text: string;
}

export interface ListResumesResponse {
  success: boolean;
  resumes: SavedResume[];
}

export interface GetResumeResponse {
  success: boolean;
  resume: SavedResumeDetail;
}

export interface SaveResumeResponse {
  success: boolean;
  resume_id: number;
}

export interface ListApplicationsResponse {
  success: boolean;
  applications: {
    id: number;
    company_name: string | null;
    job_title: string | null;
    status: string;
    created_at: string;
    resume_filename: string | null;
    original_resume_id: number | null;
  }[];
}

export interface GetApplicationResponse {
  success: boolean;
  application: Record<string, unknown>;
}
