
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { apiClient } from '../services/api';

interface ExportModalProps {
  onClose: () => void;
  onRestart: () => void;
  applicationId: number;
}

const ExportModal: React.FC<ExportModalProps> = ({ onClose, onRestart, applicationId }) => {
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
        className="bg-surface-light rounded-lg shadow-subtle w-full max-w-sm p-8 text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-semibold mb-2">Your Resume is Ready</h2>
        <p className="text-sm text-text-main/70 mb-6">Click below to download your optimized resume</p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm">
            {error}
          </div>
        )}
        
        <div className="space-y-3">
          <button 
            onClick={handleDownloadDocx}
            disabled={isDownloadingDocx}
            className="w-full bg-accent text-white h-12 rounded-lg font-medium text-sm hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloadingDocx ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating DOCX...
              </span>
            ) : (
              'Download as DOCX (Recommended)'
            )}
          </button>
          <button 
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf || true}
            className="w-full bg-surface-light border border-border-subtle h-12 rounded-lg font-medium text-sm hover:bg-surface-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Download as PDF (Coming Soon)
          </button>
        </div>

        <button onClick={onRestart} className="text-sm text-primary font-medium mt-6 hover:underline">
          Start new application
        </button>
      </motion.div>
    </motion.div>
  );
};

export default ExportModal;
