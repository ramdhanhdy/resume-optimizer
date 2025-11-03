/**
 * Form Validation Schema - InputScreen
 *
 * Comprehensive Zod schema for the main input form including
 * resume upload, job posting, and optional enhancements.
 */

import { z } from 'zod';
import { resumeFileSchema } from './resume-upload-schema';

// URL validation regex
const URL_REGEX = /^https?:\/\/.+/;
const LINKEDIN_REGEX = /^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+\/?$/;
const GITHUB_USERNAME_REGEX = /^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$/;

// Re-export resume file validation from shared schema
export { resumeFileSchema };

/**
 * Job posting input validation
 * Supports both URL and direct text input
 */
export const jobInputSchema = z
  .string({ error: 'Job posting is required' })
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
      error.issues.forEach((err) => {
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
        error: error.issues[0]?.message || 'Invalid file',
      };
    }
    return {
      isValid: false,
      error: 'An unexpected error occurred',
    };
  }
}
