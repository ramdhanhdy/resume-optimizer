import { motion } from 'framer-motion';

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
  // Color scheme based on priority
  const getPriorityColor = () => {
    if (covered === false) {
      return 'bg-gray-100 text-gray-400 border-gray-200';
    }

    if (priority === 1) {
      return variant === 'outlined'
        ? 'border-red-400 text-red-700 bg-red-50'
        : 'bg-red-100 text-red-800 border-red-200';
    }
    if (priority === 2) {
      return variant === 'outlined'
        ? 'border-blue-400 text-blue-700 bg-blue-50'
        : 'bg-blue-100 text-blue-800 border-blue-200';
    }
    if (priority === 3) {
      return variant === 'outlined'
        ? 'border-purple-400 text-purple-700 bg-purple-50'
        : 'bg-purple-100 text-purple-800 border-purple-200';
    }

    return 'bg-gray-100 text-gray-700 border-gray-200';
  };

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={onClick ? { scale: 1.05 } : {}}
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium
        border ${getPriorityColor()}
        ${onClick ? 'cursor-pointer hover:shadow-sm' : ''}
        transition-all duration-150
      `}
    >
      {/* Priority indicator */}
      {priority && covered !== false && (
        <span className="flex items-center justify-center w-4 h-4 rounded-full bg-white/60 text-[10px] font-bold">
          {priority}
        </span>
      )}

      {/* Keyword text */}
      <span className={covered === false ? 'line-through' : ''}>{keyword}</span>

      {/* Coverage indicator */}
      {covered === true && (
        <svg
          className="w-3 h-3 text-green-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={3}
            d="M5 13l4 4L19 7"
          />
        </svg>
      )}
    </motion.span>
  );
}
