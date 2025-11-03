/**
 * Form Validation Schema - Resume Upload
 *
 * Zod schema for resume file upload validation.
 */

import { z } from 'zod';

// Supported file types
const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'image/png',
  'image/jpeg',
  'image/jpg',
] as const;

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * Resume file validation schema
 */
export const resumeFileSchema = z
  .instanceof(File, { message: 'Please upload a file' })
  .refine((file) => file.size <= MAX_FILE_SIZE, {
    message: 'File size must be less than 10MB',
  })
  .refine((file) => ACCEPTED_FILE_TYPES.includes(file.type as any), {
    message: 'File must be PDF, DOCX, DOC, or image (PNG, JPG)',
  });

/**
 * Complete resume upload form schema
 */
export const resumeUploadSchema = z.object({
  resumeFile: resumeFileSchema,
});

export type ResumeUploadFormData = z.infer<typeof resumeUploadSchema>;

/**
 * Helper function to validate file client-side
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
