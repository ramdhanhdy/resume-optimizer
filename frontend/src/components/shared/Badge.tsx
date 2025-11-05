/**
 * Badge Component
 *
 * Wrapper around shadcn Badge with extended variants for backward compatibility.
 * Uses design system tokens for consistent styling.
 */

import { Badge as ShadcnBadge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  className
}: BadgeProps) {
  // Map custom variants to color classes using design tokens
  const variantClasses = {
    default: 'bg-neutral-100 text-neutral-800 border-neutral-200',
    primary: 'bg-primary/10 text-primary border-primary/20',
    success: 'bg-token-bg-success text-token-text-success border-token-border-success',
    warning: 'bg-token-bg-warning text-token-text-warning border-token-border-warning',
    danger: 'bg-token-bg-danger text-token-text-danger border-token-border-danger',
    info: 'bg-token-bg-info text-token-text-info border-token-border-info'
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs h-5',
    md: 'px-2.5 py-1 text-sm h-6',
    lg: 'px-3 py-1.5 text-base h-7'
  };

  return (
    <ShadcnBadge
      className={cn(
        'rounded-full border font-semibold',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </ShadcnBadge>
  );
}
