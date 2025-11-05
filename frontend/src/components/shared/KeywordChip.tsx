/**
 * KeywordChip Component
 *
 * Displays keywords with priority levels and coverage status.
 * Uses shadcn Badge with design tokens and accessibility features.
 */

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { scaleVariants, useReducedMotion } from '@/design-system/animations';
import { CheckIcon } from '@radix-ui/react-icons';

interface KeywordChipProps {
  keyword: string;
  priority?: 1 | 2 | 3;
  covered?: boolean;
  onClick?: () => void;
  variant?: 'default' | 'outlined';
}

export default function KeywordChip({
  keyword,
  priority,
  covered,
  onClick,
  variant = 'default'
}: KeywordChipProps) {
  const prefersReducedMotion = useReducedMotion();

  // Color scheme based on priority using design tokens
  const getPriorityColor = () => {
    if (covered === false) {
      return 'bg-muted text-muted-foreground border-border opacity-50';
    }

    if (priority === 1) {
      return variant === 'outlined'
        ? 'border-[#EF4444] text-[#991B1B] bg-[#FEE2E2]'
        : 'bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]';
    }
    if (priority === 2) {
      return variant === 'outlined'
        ? 'border-primary text-primary bg-primary/10'
        : 'bg-primary/10 text-primary border-primary/20';
    }
    if (priority === 3) {
      return variant === 'outlined'
        ? 'border-[#9333EA] text-[#6B21A8] bg-[#F3E8FF]'
        : 'bg-[#F3E8FF] text-[#6B21A8] border-[#D8B4FE]';
    }

    return 'bg-muted text-foreground border-border';
  };

  // Generate ARIA label
  const getAriaLabel = () => {
    const parts = [keyword];
    if (priority) parts.push(`priority ${priority}`);
    if (covered === true) parts.push('covered');
    if (covered === false) parts.push('not covered');
    return parts.join(', ');
  };

  const ChipContent = (
    <>
      {/* Priority indicator */}
      {priority && covered !== false && (
        <span
          className="flex items-center justify-center w-4 h-4 rounded-full bg-background/60 text-[10px] font-bold"
          aria-hidden="true"
        >
          {priority}
        </span>
      )}

      {/* Keyword text */}
      <span className={covered === false ? 'line-through' : ''}>{keyword}</span>

      {/* Coverage indicator */}
      {covered === true && (
        <CheckIcon
          className="w-3 h-3 text-[#10B981]"
          aria-label="Covered"
        />
      )}
    </>
  );

  return (
    <motion.span
      variants={prefersReducedMotion ? undefined : scaleVariants}
      initial="initial"
      animate="animate"
      whileHover={onClick && !prefersReducedMotion ? { scale: 1.05 } : {}}
      whileTap={onClick && !prefersReducedMotion ? { scale: 0.95 } : {}}
    >
      <Badge
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border min-h-[28px]',
          getPriorityColor(),
          onClick && 'cursor-pointer hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'transition-all duration-150'
        )}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
        aria-label={getAriaLabel()}
        onKeyDown={onClick ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onClick();
          }
        } : undefined}
      >
        {ChipContent}
      </Badge>
    </motion.span>
  );
}
