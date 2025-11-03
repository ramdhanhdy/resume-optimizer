/**
 * Form Validation Schema - Job Posting Input
 *
 * Zod schema for job posting text and URL validation.
 */

import { z } from 'zod';

/**
 * Job posting text validation
 */
export const jobPostingSchema = z.object({
  jobPosting: z
    .string()
    .min(50, 'Job posting must be at least 50 characters')
    .max(20000, 'Job posting must be less than 20,000 characters')
    .refine(
      (text) => {
        // Check if there's meaningful content (not just whitespace/newlines)
        const meaningfulContent = text.replace(/\s+/g, ' ').trim();
        return meaningfulContent.length >= 50;
      },
      {
        message: 'Job posting must contain at least 50 characters of meaningful content',
      }
    ),

  jobUrl: z
    .string()
    .url('Please enter a valid URL')
    .optional()
    .or(z.literal('')),

  // Optional fields for additional context
  companyName: z.string().max(200, 'Company name is too long').optional(),
  jobTitle: z.string().max(200, 'Job title is too long').optional(),
  location: z.string().max(200, 'Location is too long').optional(),
});

export type JobPostingFormData = z.infer<typeof jobPostingSchema>;

/**
 * Simplified schema for just the job posting text
 */
export const jobPostingTextSchema = z.object({
  jobPosting: jobPostingSchema.shape.jobPosting,
});

export type JobPostingTextData = z.infer<typeof jobPostingTextSchema>;

/**
 * Helper function to check if job posting has minimum viable content
 */
export function hasMinimumJobContent(text: string): boolean {
  const meaningfulContent = text.replace(/\s+/g, ' ').trim();
  return meaningfulContent.length >= 50;
}

/**
 * Helper function to extract keywords from job posting
 * (Simple implementation, can be enhanced)
 */
export function extractKeywords(text: string): string[] {
  // Remove common words and extract potential skills/keywords
  const commonWords = new Set([
    'the',
    'a',
    'an',
    'and',
    'or',
    'but',
    'in',
    'on',
    'at',
    'to',
    'for',
    'of',
    'with',
    'by',
    'from',
    'is',
    'are',
    'was',
    'were',
    'be',
    'been',
    'being',
    'have',
    'has',
    'had',
    'do',
    'does',
    'did',
    'will',
    'would',
    'should',
    'could',
    'may',
    'might',
    'must',
    'can',
  ]);

  const words = text
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter((word) => word.length > 2 && !commonWords.has(word));

  // Count word frequency
  const frequency: Record<string, number> = {};
  words.forEach((word) => {
    frequency[word] = (frequency[word] || 0) + 1;
  });

  // Return top keywords (appearing more than once)
  return Object.entries(frequency)
    .filter(([_, count]) => count > 1)
    .sort(([_, a], [__, b]) => b - a)
    .slice(0, 20)
    .map(([word]) => word);
}
