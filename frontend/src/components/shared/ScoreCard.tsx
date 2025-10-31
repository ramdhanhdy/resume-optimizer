import { motion } from 'framer-motion';

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
  // Determine color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-orange-500';
    return 'text-red-500';
  };

  const getBgGradient = (score: number): string => {
    if (score >= 80) return 'from-green-50 to-green-100';
    if (score >= 60) return 'from-blue-50 to-blue-100';
    if (score >= 40) return 'from-orange-50 to-orange-100';
    return 'from-red-50 to-red-100';
  };

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4',
    large: 'p-6'
  };

  const scoreSizeClasses = {
    small: 'text-2xl',
    medium: 'text-3xl',
    large: 'text-5xl'
  };

  const titleSizeClasses = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={onClick ? { scale: 1.02 } : {}}
      onClick={onClick}
      className={`
        ${sizeClasses[size]}
        ${gradient ? `bg-gradient-to-br ${getBgGradient(score)}` : 'bg-white'}
        border border-gray-200 rounded-lg shadow-sm
        ${onClick ? 'cursor-pointer hover:shadow-md' : ''}
        transition-all duration-200
      `}
    >
      <div className="flex flex-col items-center text-center">
        {/* Score */}
        <div className={`${scoreSizeClasses[size]} font-bold ${getScoreColor(score)}`}>
          {score}{showPercentage && '%'}
        </div>

        {/* Title */}
        <div className={`${titleSizeClasses[size]} text-gray-600 font-medium mt-1`}>
          {title}
        </div>

        {/* Subtitle */}
        {subtitle && (
          <div className="text-xs text-gray-500 mt-1">
            {subtitle}
          </div>
        )}
      </div>

      {/* Progress bar */}
      {size !== 'small' && (
        <div className="mt-3 w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${score}%` }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className={`h-full ${
              score >= 80 ? 'bg-green-500' :
              score >= 60 ? 'bg-blue-500' :
              score >= 40 ? 'bg-orange-500' :
              'bg-red-500'
            }`}
          />
        </div>
      )}
    </motion.div>
  );
}
