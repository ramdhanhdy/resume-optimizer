/**
 * Recovery Banner Component
 *
 * Displays when user has preserved session data.
 * Uses design tokens, ARIA live regions, and accessible patterns.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { slideDownVariants, collapseVariants, useReducedMotion } from '@/design-system/animations';
import { RecoverySession } from '../../services/storage';

interface RecoveryBannerProps {
  session: RecoverySession;
  onRetry: () => void;
  onStartFresh: () => void;
  isRetrying?: boolean;
}

export default function RecoveryBanner({
  session,
  onRetry,
  onStartFresh,
  isRetrying = false,
}: RecoveryBannerProps) {
  const [showDetails, setShowDetails] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  const errorMessage = session.errorContext?.errorMessage || 'An error occurred during processing';
  const timeAgo = formatTimeAgo(session.createdAt);

  // Determine banner color based on error category using design tokens
  const getBannerStyle = () => {
    switch (session.errorContext?.category) {
      case 'TRANSIENT':
        return {
          bg: 'bg-[#DBEAFE]',
          border: 'border-[#60A5FA]',
          text: 'text-[#1E3A8A]',
          icon: 'text-[#2563EB]',
        };
      case 'PERMANENT':
        return {
          bg: 'bg-destructive/10',
          border: 'border-destructive',
          text: 'text-destructive',
          icon: 'text-destructive',
        };
      default:
        return {
          bg: 'bg-[#FEF3C7]',
          border: 'border-[#FBBF24]',
          text: 'text-[#78350F]',
          icon: 'text-[#D97706]',
        };
    }
  };

  const style = getBannerStyle();

  // Get ARIA role based on severity
  const getAriaRole = () => {
    switch (session.errorContext?.category) {
      case 'PERMANENT':
        return 'alert';
      default:
        return 'status';
    }
  };

  return (
    <motion.div
      variants={prefersReducedMotion ? undefined : slideDownVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={cn(
        style.bg,
        'border-l-4',
        style.border,
        'p-4 mb-6 rounded-r-lg shadow-sm'
      )}
      role={getAriaRole()}
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex items-start">
        <AlertCircle
          className={cn('w-5 h-5', style.icon, 'mt-0.5 flex-shrink-0')}
          aria-hidden="true"
        />

        <div className="ml-3 flex-1">
          <h3 className={cn('text-sm font-semibold', style.text)}>
            {session.errorContext?.category === 'TRANSIENT' && 'Temporary Error Occurred'}
            {session.errorContext?.category === 'RECOVERABLE' && 'Error During Processing'}
            {session.errorContext?.category === 'PERMANENT' && 'Action Required'}
            {!session.errorContext && 'Session Recovered'}
          </h3>

          <p className={cn('text-sm', style.text, 'mt-1 opacity-90')}>
            Your data from <strong>{timeAgo}</strong> has been preserved.
          </p>

          <p className={cn('text-sm', style.text, 'mt-2')}>
            {errorMessage}
          </p>

          {/* Details Section */}
          <AnimatePresence>
            {showDetails && session.errorContext && (
              <motion.div
                variants={collapseVariants}
                initial="collapsed"
                animate="expanded"
                exit="collapsed"
                className={cn(
                  'mt-3 p-3 rounded text-xs font-mono',
                  style.bg,
                  'bg-opacity-50',
                  style.text
                )}
                aria-label="Error details"
              >
                <div className="space-y-1">
                  <div><span className="font-semibold">Error ID:</span> {session.errorContext.errorId}</div>
                  <div><span className="font-semibold">Type:</span> {session.errorContext.errorType}</div>
                  <div><span className="font-semibold">Category:</span> {session.errorContext.category}</div>
                  <div><span className="font-semibold">Occurred:</span> {new Date(session.errorContext.occurredAt).toLocaleString()}</div>
                  {session.errorContext.retryCount > 0 && (
                    <div><span className="font-semibold">Retry Attempts:</span> {session.errorContext.retryCount}</div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* File Info */}
          {session.fileMetadata && (
            <div className={cn('mt-3 text-xs', style.text, 'opacity-75')}>
              File preserved: <strong>{session.fileMetadata.fileName}</strong> ({formatFileSize(session.fileMetadata.fileSize)})
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-4 flex flex-wrap gap-3">
            {session.recovery.canManualRetry && (
              <Button
                onClick={onRetry}
                disabled={isRetrying}
                variant="outline"
                className={cn(
                  'border-2',
                  style.border,
                  style.text
                )}
                aria-label="Retry processing the resume"
              >
                {isRetrying ? (
                  <>
                    <motion.div
                      animate={{ rotate: prefersReducedMotion ? 0 : 360 }}
                      transition={{
                        duration: prefersReducedMotion ? 0 : 1,
                        repeat: prefersReducedMotion ? 0 : Infinity,
                        ease: 'linear'
                      }}
                      className="w-4 h-4 border-2 border-current border-t-transparent rounded-full mr-2"
                      aria-hidden="true"
                    />
                    <span>Retrying...</span>
                  </>
                ) : (
                  'Retry Processing'
                )}
              </Button>
            )}

            <Button
              onClick={onStartFresh}
              disabled={isRetrying}
              variant="outline"
              className={cn(style.border, style.text, 'opacity-75 hover:opacity-100')}
              aria-label="Dismiss session and start fresh"
            >
              Start Fresh
            </Button>

            <Button
              onClick={() => setShowDetails(!showDetails)}
              variant="ghost"
              size="sm"
              className={cn(style.text, 'hover:opacity-75')}
              aria-expanded={showDetails}
              aria-controls="error-details"
              aria-label={showDetails ? 'Hide error details' : 'Show error details'}
            >
              {showDetails ? (
                <>
                  Hide Details
                  <ChevronUp className="w-4 h-4 ml-1" aria-hidden="true" />
                </>
              ) : (
                <>
                  Show Details
                  <ChevronDown className="w-4 h-4 ml-1" aria-hidden="true" />
                </>
              )}
            </Button>
          </div>

          {/* Support Reference */}
          <p className={cn('text-xs', style.text, 'opacity-60 mt-3')}>
            Support Reference: {session.recovery.supportReferenceId}
          </p>
        </div>

        {/* Close Button */}
        <Button
          onClick={onStartFresh}
          variant="ghost"
          size="icon"
          className={cn(style.text, 'hover:opacity-75 ml-2 h-8 w-8')}
          aria-label="Dismiss session and start fresh"
        >
          <X className="w-5 h-5" />
        </Button>
      </div>
    </motion.div>
  );
}

/**
 * Format timestamp to relative time
 */
function formatTimeAgo(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  return `${Math.floor(seconds / 86400)} days ago`;
}

/**
 * Format file size to human readable
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
