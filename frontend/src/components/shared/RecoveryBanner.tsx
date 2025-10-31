/**
 * Recovery Banner Component
 * Displays when user has preserved session data
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X, ChevronDown, ChevronUp } from 'lucide-react';
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

  const errorMessage = session.errorContext?.errorMessage || 'An error occurred during processing';
  const timeAgo = formatTimeAgo(session.createdAt);

  // Determine banner color based on error category
  const getBannerStyle = () => {
    switch (session.errorContext?.category) {
      case 'TRANSIENT':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-400',
          text: 'text-blue-900',
          icon: 'text-blue-600',
        };
      case 'PERMANENT':
        return {
          bg: 'bg-red-50',
          border: 'border-red-400',
          text: 'text-red-900',
          icon: 'text-red-600',
        };
      default:
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-400',
          text: 'text-yellow-900',
          icon: 'text-yellow-600',
        };
    }
  };

  const style = getBannerStyle();

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`${style.bg} border-l-4 ${style.border} p-4 mb-6 rounded-r-lg shadow-sm`}
    >
      <div className="flex items-start">
        <AlertCircle className={`w-5 h-5 ${style.icon} mt-0.5 flex-shrink-0`} />

        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-semibold ${style.text}`}>
            {session.errorContext?.category === 'TRANSIENT' && 'Temporary Error Occurred'}
            {session.errorContext?.category === 'RECOVERABLE' && 'Error During Processing'}
            {session.errorContext?.category === 'PERMANENT' && 'Action Required'}
            {!session.errorContext && 'Session Recovered'}
          </h3>

          <p className={`text-sm ${style.text} mt-1 opacity-90`}>
            Your data from <strong>{timeAgo}</strong> has been preserved.
          </p>

          <p className={`text-sm ${style.text} mt-2`}>
            {errorMessage}
          </p>

          {/* Details Section */}
          <AnimatePresence>
            {showDetails && session.errorContext && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={`mt-3 p-3 ${style.bg} bg-opacity-50 rounded text-xs font-mono ${style.text}`}
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
            <div className={`mt-3 text-xs ${style.text} opacity-75`}>
              File preserved: <strong>{session.fileMetadata.fileName}</strong> ({formatFileSize(session.fileMetadata.fileSize)})
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-4 flex flex-wrap gap-3">
            {session.recovery.canManualRetry && (
              <button
                onClick={onRetry}
                disabled={isRetrying}
                className={`px-4 py-2 bg-white border-2 ${style.border} ${style.text} rounded-lg font-medium hover:bg-opacity-80 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2`}
              >
                {isRetrying ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                    />
                    Retrying...
                  </>
                ) : (
                  'Retry Processing'
                )}
              </button>
            )}

            <button
              onClick={onStartFresh}
              disabled={isRetrying}
              className={`px-4 py-2 bg-white border ${style.border} ${style.text} opacity-75 rounded-lg font-medium hover:opacity-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all`}
            >
              Start Fresh
            </button>

            <button
              onClick={() => setShowDetails(!showDetails)}
              className={`px-3 py-2 ${style.text} hover:opacity-75 text-sm flex items-center gap-1 transition-opacity`}
            >
              {showDetails ? (
                <>
                  Hide Details
                  <ChevronUp className="w-4 h-4" />
                </>
              ) : (
                <>
                  Show Details
                  <ChevronDown className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Support Reference */}
          <p className={`text-xs ${style.text} opacity-60 mt-3`}>
            Support Reference: {session.recovery.supportReferenceId}
          </p>
        </div>

        {/* Close Button */}
        <button
          onClick={onStartFresh}
          className={`${style.text} hover:opacity-75 transition-opacity ml-2`}
          title="Dismiss and start fresh"
        >
          <X className="w-5 h-5" />
        </button>
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
