/**
 * Form Validation Hook
 *
 * Wrapper around React Hook Form with Zod validation and error handling.
 */

import { useForm, UseFormProps, UseFormReturn, FieldValues } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

/**
 * Enhanced form validation hook with Zod schema integration
 *
 * @example
 * const form = useFormValidation({
 *   schema: myZodSchema,
 *   defaultValues: { name: '' },
 * });
 */
export function useFormValidation<TFieldValues extends FieldValues = FieldValues>(
  schema: z.ZodType<TFieldValues>,
  options?: Omit<UseFormProps<TFieldValues>, 'resolver'>
): UseFormReturn<TFieldValues> {
  return useForm<TFieldValues>({
    ...options,
    resolver: zodResolver(schema) as any,
    mode: options?.mode || 'onBlur', // Validate on blur by default
  }) as UseFormReturn<TFieldValues>;
}

/**
 * Extract field error message
 * @param form - Form instance from useFormValidation
 * @param fieldName - Name of the field
 * @returns Error message or undefined
 */
export function getFieldError<TFieldValues extends FieldValues>(
  form: UseFormReturn<TFieldValues>,
  fieldName: keyof TFieldValues
): string | undefined {
  const error = form.formState.errors[fieldName];
  return error?.message as string | undefined;
}

/**
 * Check if field has error
 */
export function hasFieldError<TFieldValues extends FieldValues>(
  form: UseFormReturn<TFieldValues>,
  fieldName: keyof TFieldValues
): boolean {
  return !!form.formState.errors[fieldName];
}

/**
 * Get field state (valid, invalid, idle)
 */
export function getFieldState<TFieldValues extends FieldValues>(
  form: UseFormReturn<TFieldValues>,
  fieldName: keyof TFieldValues
): 'valid' | 'invalid' | 'idle' {
  const { errors, touchedFields, dirtyFields } = form.formState;
  const isTouched = touchedFields[fieldName as string];
  const isDirty = dirtyFields[fieldName as string];
  const hasError = !!errors[fieldName];

  if (!isTouched && !isDirty) return 'idle';
  if (hasError) return 'invalid';
  return 'valid';
}

/**
 * Format Zod error for display
 */
export function formatZodError(error: z.ZodError): string[] {
  return error.issues.map((err) => err.message);
}

/**
 * Validate data against schema without form
 */
export function validateWithSchema<T>(
  schema: z.ZodType<T>,
  data: unknown
): { success: true; data: T } | { success: false; errors: string[] } {
  try {
    const result = schema.parse(data);
    return { success: true, data: result };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, errors: formatZodError(error) };
    }
    return { success: false, errors: ['An unexpected error occurred'] };
  }
}
