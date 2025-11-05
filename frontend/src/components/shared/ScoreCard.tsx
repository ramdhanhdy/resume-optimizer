/**
 * ScoreCard Component
 *
 * Displays a score with visual indicators and progress bar.
 * Uses design tokens, shadcn Card, and centralized animations.
 */

import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { slideUpVariants, useReducedMotion } from '@/design-system/animations';
import { colors, spacing } from '@/design-system/tokens';

interface ScoreCardProps {
  title: string;
  score: number;
  subtitle?: string;
  size?: 'small' | 'medium' | 'large';
  showPercentage?: boolean;
  gradient?: boolean;
  onClick?: () => void;
}

export default function ScoreCard({
  title,
  score,
  subtitle,
  size = 'medium',
  showPercentage = true,
  gradient = false,
  onClick
}: ScoreCardProps) {
  const prefersReducedMotion = useReducedMotion();

  // Determine color based on score using design tokens
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-[#10B981]'; // success color
    if (score >= 60) return 'text-primary';
    if (score >= 40) return 'text-[#FF9500]'; // warning color
    return 'text-[#EF4444]'; // error color
  };

  const getProgressColor = (score: number): string => {
    if (score >= 80) return 'bg-[#10B981]';
    if (score >= 60) return 'bg-primary';
    if (score >= 40) return 'bg-[#FF9500]';
    return 'bg-[#EF4444]';
  };

  const getBgGradient = (score: number): string => {
    if (score >= 80) return 'from-[#D1FAE5] to-[#A7F3D0]';
    if (score >= 60) return 'from-blue-50 to-blue-100';
    if (score >= 40) return 'from-[#FEF3C7] to-[#FDE68A]';
    return 'from-[#FEE2E2] to-[#FECACA]';
  };

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4 sm:p-6',
    large: 'p-6 sm:p-8'
  };

  const scoreSizeClasses = {
    small: 'text-2xl',
    medium: 'text-3xl sm:text-4xl',
    large: 'text-4xl sm:text-5xl'
  };

  const titleSizeClasses = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  return (
    <motion.div
      variants={prefersReducedMotion ? undefined : slideUpVariants}
      initial="initial"
      animate="animate"
      whileHover={onClick && !prefersReducedMotion ? { scale: 1.02 } : {}}
      whileTap={onClick && !prefersReducedMotion ? { scale: 0.98 } : {}}
    >
      <Card
        onClick={onClick}
        className={cn(
          sizeClasses[size],
          gradient && `bg-gradient-to-br ${getBgGradient(score)}`,
          onClick && 'cursor-pointer hover:shadow-lg transition-shadow duration-200',
          'min-h-[120px]'
        )}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
        aria-label={onClick ? `${title}: ${score}${showPercentage ? '%' : ''} score. Click for details.` : undefined}
      >
        <div className="flex flex-col items-center text-center">
          {/* Score */}
          <div
            className={cn(
              scoreSizeClasses[size],
              'font-bold',
              getScoreColor(score)
            )}
            aria-label={`Score: ${score}${showPercentage ? ' percent' : ''}`}
          >
            {score}{showPercentage && '%'}
          </div>

          {/* Title */}
          <div className={cn(titleSizeClasses[size], 'text-foreground/80 font-medium mt-1')}>
            {title}
          </div>

          {/* Subtitle */}
          {subtitle && (
            <div className="text-xs text-muted-foreground mt-1">
              {subtitle}
            </div>
          )}
        </div>

        {/* Progress bar */}
        {size !== 'small' && (
          <div
            className="mt-3 w-full bg-muted rounded-full h-1.5 overflow-hidden"
            role="progressbar"
            aria-valuenow={score}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${title} progress: ${score}%`}
          >
            <motion.div
              initial={{ width: prefersReducedMotion ? `${score}%` : 0 }}
              animate={{ width: `${score}%` }}
              transition={{
                duration: prefersReducedMotion ? 0 : 0.8,
                delay: prefersReducedMotion ? 0 : 0.2,
                ease: [0.4, 0.0, 0.2, 1]
              }}
              className={cn('h-full', getProgressColor(score))}
            />
          </div>
        )}
      </Card>
    </motion.div>
  );
}
