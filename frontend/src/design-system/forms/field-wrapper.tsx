/**
 * Field Wrapper Component
 *
 * Consistent wrapper for form fields with label, error, and help text.
 * Integrates with React Hook Form and shadcn Field component.
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface FieldWrapperProps {
  /** Field label */
  label?: string;

  /** Field ID (for htmlFor connection) */
  id?: string;

  /** Error message to display */
  error?: string;

  /** Help text (shown below the field when no error) */
  helpText?: string;

  /** Whether the field is required */
  required?: boolean;

  /** Whether the field is disabled */
  disabled?: boolean;

  /** Children (the actual input/select/textarea) */
  children: React.ReactNode;

  /** Additional className for wrapper */
  className?: string;

  /** Layout direction */
  layout?: 'vertical' | 'horizontal';
}

/**
 * Consistent field wrapper with label, error, and help text
 */
export function FieldWrapper({
  label,
  id,
  error,
  helpText,
  required,
  disabled,
  children,
  className,
  layout = 'vertical',
}: FieldWrapperProps) {
  const hasError = !!error;
  const showHelp = !hasError && !!helpText;

  return (
    <div
      className={cn(
        'field-wrapper',
        layout === 'horizontal' ? 'flex items-center gap-4' : 'space-y-2',
        className
      )}
    >
      {/* Label */}
      {label && (
        <label
          htmlFor={id}
          className={cn(
            'block text-sm font-medium',
            hasError ? 'text-error' : 'text-foreground',
            disabled && 'opacity-50 cursor-not-allowed',
            layout === 'horizontal' && 'min-w-[120px]'
          )}
        >
          {label}
          {required && (
            <span className="text-error ml-1" aria-label="required">
              *
            </span>
          )}
        </label>
      )}

      {/* Field Container */}
      <div className={cn('field-container', layout === 'horizontal' && 'flex-1')}>
        {/* Input/Field */}
        <div
          className={cn(
            hasError && 'field-error',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          {children}
        </div>

        {/* Error Message */}
        {hasError && (
          <p
            className="text-sm text-error mt-1.5 flex items-center gap-1"
            role="alert"
            aria-live="polite"
          >
            <span aria-hidden="true">⚠</span>
            {error}
          </p>
        )}

        {/* Help Text */}
        {showHelp && (
          <p className="text-sm text-muted-foreground mt-1.5">{helpText}</p>
        )}
      </div>
    </div>
  );
}

/**
 * Field Group Component
 * Groups related fields together with optional legend
 */
export interface FieldGroupProps {
  /** Group legend/title */
  legend?: string;

  /** Group description */
  description?: string;

  /** Children fields */
  children: React.ReactNode;

  /** Additional className */
  className?: string;
}

export function FieldGroup({
  legend,
  description,
  children,
  className,
}: FieldGroupProps) {
  return (
    <fieldset className={cn('field-group border-none p-0', className)}>
      {legend && (
        <legend className="text-lg font-semibold text-foreground mb-4">
          {legend}
        </legend>
      )}
      {description && (
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
      )}
      <div className="space-y-4">{children}</div>
    </fieldset>
  );
}

/**
 * Inline Field Wrapper
 * For inline form layouts (checkbox, radio, etc.)
 */
export interface InlineFieldWrapperProps {
  /** Field label (appears after the input) */
  label: string;

  /** Field ID */
  id?: string;

  /** Error message */
  error?: string;

  /** Whether the field is disabled */
  disabled?: boolean;

  /** Children (typically checkbox or radio) */
  children: React.ReactNode;

  /** Additional className */
  className?: string;
}

export function InlineFieldWrapper({
  label,
  id,
  error,
  disabled,
  children,
  className,
}: InlineFieldWrapperProps) {
  const hasError = !!error;

  return (
    <div className={cn('inline-field-wrapper', className)}>
      <div className="flex items-center gap-2">
        {children}
        <label
          htmlFor={id}
          className={cn(
            'text-sm font-medium cursor-pointer',
            hasError ? 'text-error' : 'text-foreground',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          {label}
        </label>
      </div>

      {hasError && (
        <p
          className="text-sm text-error mt-1.5 ml-6 flex items-center gap-1"
          role="alert"
          aria-live="polite"
        >
          <span aria-hidden="true">⚠</span>
          {error}
        </p>
      )}
    </div>
  );
}
