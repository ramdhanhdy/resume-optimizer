/**
 * Export Modal Component
 *
 * Modal for exporting optimized resumes with accessible design.
 * Uses shadcn Dialog with proper ARIA attributes and keyboard navigation.
 */

import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { apiClient } from '../services/api';
import { useEscapeKey } from '@/hooks';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRestart: () => void;
  applicationId: number;
}

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose, onRestart, applicationId }) => {
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Close modal on Escape key
  useEscapeKey(onClose);

  // Reset transient state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setError(null);
      setIsDownloadingDocx(false);
      setIsDownloadingPdf(false);
    }
  }, [isOpen]);

  const handleDownloadDocx = async () => {
    try {
      setError(null);
      setIsDownloadingDocx(true);

      // Call the export API which will execute the LLM-generated DOCX code
      const blob = await apiClient.exportResume(applicationId, 'docx');

      // Create a download link and trigger it
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `resume_${applicationId}.docx`;
      link.setAttribute('aria-label', 'Download optimized resume as DOCX');
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      console.error('Failed to download DOCX:', err);
      setError(err instanceof Error ? err.message : 'Failed to download DOCX');
    } finally {
      setIsDownloadingDocx(false);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      setError(null);
      setIsDownloadingPdf(true);

      // PDF export not yet implemented
      setError('PDF export is not yet available. Please use DOCX format.');

    } catch (err) {
      console.error('Failed to download PDF:', err);
      setError(err instanceof Error ? err.message : 'Failed to download PDF');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center sm:text-center">
          <DialogTitle className="text-xl">Your Resume is Ready</DialogTitle>
          <DialogDescription>
            Click below to download your optimized resume
          </DialogDescription>
        </DialogHeader>

        {/* Error Alert */}
        {error && (
          <div
            className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm"
            role="alert"
            aria-live="polite"
          >
            {error}
          </div>
        )}

        {/* Download Buttons */}
        <div className="space-y-3">
          <Button
            onClick={handleDownloadDocx}
            disabled={isDownloadingDocx}
            className="w-full h-12 bg-accent hover:bg-accent/90 text-white"
            aria-label="Download resume as DOCX file"
          >
            {isDownloadingDocx ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Generating DOCX...</span>
              </span>
            ) : (
              'Download as DOCX (Recommended)'
            )}
          </Button>

          <Button
            onClick={handleDownloadPdf}
            disabled={true}
            variant="outline"
            className="w-full h-12"
            aria-label="Download resume as PDF (coming soon)"
            aria-disabled="true"
          >
            Download as PDF (Coming Soon)
          </Button>
        </div>

        <DialogFooter className="sm:justify-center">
          <Button
            onClick={onRestart}
            variant="link"
            className="text-primary font-medium"
            aria-label="Start a new resume optimization"
          >
            Start new application
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ExportModal;
