/**
 * Form Validation Schema - InputScreen
 *
 * Comprehensive Zod schema for the main input form including
 * resume upload, job posting, and optional enhancements.
 */

import { z } from 'zod';

// URL validation regex
const URL_REGEX = /^https?:\/\/.+/;
const LINKEDIN_REGEX = /^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+\/?$/;
const GITHUB_USERNAME_REGEX = /^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$/;

/**
 * File size and type constraints
 */
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'image/png',
  'image/jpeg',
  'image/jpg',
] as const;

/**
 * Resume file validation
 */
export const resumeFileSchema = z
  .instanceof(File, { message: 'Please upload a resume file' })
  .refine((file) => file.size > 0, {
    message: 'File cannot be empty',
  })
  .refine((file) => file.size <= MAX_FILE_SIZE, {
    message: 'File size must be less than 10MB',
  })
  .refine((file) => ACCEPTED_FILE_TYPES.includes(file.type as any), {
    message: 'File must be PDF, DOCX, DOC, or image (PNG, JPG)',
  });

/**
 * Job posting input validation
 * Supports both URL and direct text input
 */
export const jobInputSchema = z
  .string({ required_error: 'Job posting is required' })
  .min(1, 'Job posting cannot be empty')
  .refine(
    (value) => {
      // If it's a URL, validate URL format
      if (value.startsWith('http://') || value.startsWith('https://')) {
        return URL_REGEX.test(value);
      }
      // If it's text, ensure meaningful content
      const meaningfulContent = value.replace(/\s+/g, ' ').trim();
      return meaningfulContent.length >= 50;
    },
    {
      message: 'Job posting must be a valid URL or at least 50 characters of text',
    }
  );

/**
 * LinkedIn URL validation
 */
export const linkedinUrlSchema = z
  .string()
  .optional()
  .refine(
    (value) => {
      if (!value || value.trim() === '') return true;
      return LINKEDIN_REGEX.test(value);
    },
    {
      message: 'Please enter a valid LinkedIn profile URL (e.g., https://linkedin.com/in/yourname)',
    }
  );

/**
 * GitHub username validation
 */
export const githubUsernameSchema = z
  .string()
  .optional()
  .refine(
    (value) => {
      if (!value || value.trim() === '') return true;
      return GITHUB_USERNAME_REGEX.test(value);
    },
    {
      message: 'Please enter a valid GitHub username (letters, numbers, hyphens; max 39 chars)',
    }
  );

/**
 * GitHub token validation (basic format check)
 */
export const githubTokenSchema = z
  .string()
  .optional()
  .refine(
    (value) => {
      if (!value || value.trim() === '') return true;
      // GitHub tokens start with ghp_, gho_, ghu_, ghs_, or ghr_
      return /^gh[pousr]_[a-zA-Z0-9]{36,}$/.test(value);
    },
    {
      message: 'Please enter a valid GitHub personal access token (starts with ghp_)',
    }
  );

/**
 * Complete InputScreen form schema
 */
export const inputScreenSchema = z.object({
  // Required fields
  resumeFile: resumeFileSchema.optional(), // File handled separately in form
  jobInput: jobInputSchema,

  // Optional enhancement fields
  linkedinUrl: linkedinUrlSchema,
  githubUsername: githubUsernameSchema,
  githubToken: githubTokenSchema,
});

export type InputScreenFormData = z.infer<typeof inputScreenSchema>;

/**
 * Helper function to determine if job input is a URL
 */
export function isJobUrl(jobInput: string): boolean {
  return jobInput.startsWith('http://') || jobInput.startsWith('https://');
}

/**
 * Helper function to validate the entire form data
 */
export function validateInputScreenForm(
  data: Partial<InputScreenFormData>
): {
  isValid: boolean;
  errors?: Record<string, string>;
} {
  try {
    inputScreenSchema.parse(data);
    return { isValid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {};
      error.errors.forEach((err) => {
        const path = err.path.join('.');
        errors[path] = err.message;
      });
      return {
        isValid: false,
        errors,
      };
    }
    return {
      isValid: false,
      errors: { general: 'An unexpected validation error occurred' },
    };
  }
}

/**
 * Helper to extract meaningful text from job posting
 */
export function extractJobText(jobInput: string): string {
  return jobInput.replace(/\s+/g, ' ').trim();
}

/**
 * Helper function to validate resume file client-side
 */
export function validateResumeFile(file: File): {
  isValid: boolean;
  error?: string;
} {
  try {
    resumeFileSchema.parse(file);
    return { isValid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        isValid: false,
        error: error.errors[0]?.message || 'Invalid file',
      };
    }
    return {
      isValid: false,
      error: 'An unexpected error occurred',
    };
  }
}
