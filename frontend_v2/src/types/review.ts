export interface ReviewResume {
  filename: string;
  plain_text: string;
  markdown: string;
}

export interface ReviewExports {
  docx_url?: string;
  pdf_url?: string;
}

export interface ApplicationReview {
  application_id: number;
  status: string;
  resume: ReviewResume;
  summary_points: string[];
  exports: ReviewExports;
}
