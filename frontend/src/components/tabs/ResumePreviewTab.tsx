import { useState } from 'react';
import { apiClient } from '../../services/api';
import { Button } from '@/components/ui/button';

interface ResumePreviewTabProps {
  resumeText: string;
  applicationId: number;
}

export default function ResumePreviewTab({ resumeText, applicationId }: ResumePreviewTabProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      const blob = await apiClient.exportResume(applicationId, 'docx');
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `resume_${applicationId}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download:', err);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <>
      {/* Action bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <p className="text-sm text-text-main/60">
          Plain text preview • Download DOCX for formatted version
        </p>
        <Button
          onClick={handleDownload}
          disabled={isDownloading}
          className="bg-accent hover:bg-accent/90 text-white w-full sm:w-auto"
          aria-label="Download optimized resume as DOCX file"
        >
          {isDownloading ? (
            <>
              <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Downloading...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Download DOCX</span>
            </>
          )}
        </Button>
      </div>

      {/* Resume preview */}
      <div className="bg-surface-light border border-border-subtle rounded-lg shadow-subtle" role="article" aria-label="Resume text preview">
        <div className="max-h-[600px] sm:max-h-[800px] overflow-auto">
          <div className="p-6 sm:p-8 md:p-12">
            <pre className="font-mono text-xs sm:text-sm text-text-main whitespace-pre-wrap leading-relaxed">
              {resumeText || 'No resume text available'}
            </pre>
          </div>
        </div>
      </div>

      {/* Info box */}
      <div className="mt-4 bg-primary/5 border border-primary/10 rounded-lg p-4" role="note" aria-label="Preview information">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-text-main/70">
            This preview shows plain text only. The DOCX file includes professional formatting, proper spacing, and ATS-optimized styling.
          </p>
        </div>
      </div>
    </>
  );
}
