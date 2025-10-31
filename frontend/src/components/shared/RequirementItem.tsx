import { motion } from 'framer-motion';
import { useState } from 'react';

interface RequirementItemProps {
  requirement: string;
  status: 'covered' | 'partial' | 'missing';
  assessment?: string;
  isRequired?: boolean;
}

export default function RequirementItem({
  requirement,
  status,
  assessment,
  isRequired = false
}: RequirementItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusConfig = () => {
    switch (status) {
      case 'covered':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ),
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          iconColor: 'text-green-600',
          textColor: 'text-green-900'
        };
      case 'partial':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          iconColor: 'text-yellow-600',
          textColor: 'text-yellow-900'
        };
      case 'missing':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          iconColor: 'text-red-600',
          textColor: 'text-red-900'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`
        ${config.bgColor} ${config.borderColor}
        border rounded-lg p-3
        transition-all duration-200
      `}
    >
      <div className="flex items-start gap-3">
        {/* Status icon */}
        <div className={`flex-shrink-0 ${config.iconColor}`}>
          {config.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className={`text-sm font-medium ${config.textColor}`}>
                  {requirement}
                </p>
                {isRequired && (
                  <span className="px-1.5 py-0.5 text-[10px] font-semibold text-red-700 bg-red-100 rounded">
                    REQUIRED
                  </span>
                )}
              </div>

              {/* Assessment (expandable if present) */}
              {assessment && (
                <div className="mt-1">
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-xs text-gray-600 hover:text-gray-800 font-medium underline"
                  >
                    {isExpanded ? 'Hide details' : 'Show details'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Expanded assessment */}
          {isExpanded && assessment && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2 pt-2 border-t border-gray-200"
            >
              <p className="text-xs text-gray-700 whitespace-pre-wrap">
                {assessment}
              </p>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
