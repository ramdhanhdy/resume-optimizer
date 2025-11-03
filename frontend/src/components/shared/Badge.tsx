/**
 * Badge Component
 *
 * Wrapper around shadcn Badge with extended variants for backward compatibility.
 * Uses design system tokens for consistent styling.
 */

import { Badge as ShadcnBadge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { colors } from '@/design-system/tokens';

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
    success: 'bg-[#D1FAE5] text-[#065F46] border-[#6EE7B7]',
    warning: 'bg-[#FEF3C7] text-[#92400E] border-[#FCD34D]',
    danger: 'bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]',
    info: 'bg-[#DBEAFE] text-[#1E40AF] border-[#93C5FD]'
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
