/**
 * FormField Component
 *
 * Accessible form field combining Label + Input + Error message.
 * Integrates with React Hook Form.
 */

import * as React from 'react';
import { Label } from './label';
import { Input } from './input';
import { cn } from '@/lib/utils';

export interface FormFieldProps
  extends Omit<React.ComponentProps<'input'>, 'id'> {
  /** Field label text */
  label?: string;
  /** Unique field ID (auto-generated if not provided) */
  id?: string;
  /** Error message to display */
  error?: string;
  /** Optional helper text */
  helperText?: string;
  /** Icon to display before label */
  icon?: React.ReactNode;
  /** Whether the field is required */
  required?: boolean;
  /** Additional className for the container */
  containerClassName?: string;
}

const FormField = React.forwardRef<HTMLInputElement, FormFieldProps>(
  (
    {
      label,
      id,
      error,
      helperText,
      icon,
      required,
      containerClassName,
      className,
      ...props
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const fieldId = id || React.useId();
    const errorId = `${fieldId}-error`;
    const helperId = `${fieldId}-helper`;

    return (
      <div className={cn('space-y-2', containerClassName)}>
        {/* Label */}
        {label && (
          <Label
            htmlFor={fieldId}
            className={cn(
              'flex items-center gap-2 text-sm font-semibold text-foreground',
              error && 'text-destructive'
            )}
          >
            {icon && <span className="flex-shrink-0">{icon}</span>}
            <span>{label}</span>
            {required && (
              <span className="text-destructive" aria-label="required">
                *
              </span>
            )}
            {!required && props.placeholder && (
              <span className="text-muted-foreground font-normal text-xs">
                (optional)
              </span>
            )}
          </Label>
        )}

        {/* Input */}
        <Input
          id={fieldId}
          ref={ref}
          className={cn(
            error &&
              'border-destructive focus-visible:ring-destructive',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={cn(
            error && errorId,
            helperText && !error && helperId
          )}
          {...props}
        />

        {/* Error Message */}
        {error && (
          <p
            id={errorId}
            className="text-sm text-destructive font-medium"
            role="alert"
            aria-live="polite"
          >
            {error}
          </p>
        )}

        {/* Helper Text */}
        {helperText && !error && (
          <p
            id={helperId}
            className="text-xs text-muted-foreground leading-relaxed"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

FormField.displayName = 'FormField';

export { FormField };
