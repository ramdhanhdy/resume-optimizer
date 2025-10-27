
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadIcon, CheckIcon } from './icons';

interface InputScreenProps {
  onStart: (data: { resumeText: string; jobInput: string; isUrl: boolean }) => void;
}

const InputScreen: React.FC<InputScreenProps> = ({ onStart }) => {
  const [fileName, setFileName] = useState<string>('');
  const [resumeText, setResumeText] = useState<string>('');
  const [jobInput, setJobInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isReady = !!fileName && !!jobInput;

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      setFileName(file.name);
      setIsLoading(true);
      
      try {
        const { apiClient } = await import('../services/api');
        const response = await apiClient.uploadResume(file);
        setResumeText(response.text);
      } catch (error) {
        console.error('Failed to upload resume:', error);
        alert('Failed to upload resume. Please try again.');
        setFileName('');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };
  
  const handleContinue = () => {
    // Defensive check: don't proceed without valid data
    if (isReady && resumeText && resumeText.trim().length > 10) {
      const isUrl = jobInput.startsWith('http://') || jobInput.startsWith('https://');
      onStart({ resumeText, jobInput, isUrl });
    } else {
      console.warn('Cannot continue: missing resume text or job input');
    }
  };

  // Auto-advance removed - user must manually click Continue button for better UX

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
      className="min-h-screen flex items-center justify-center p-8"
    >
      <div className="w-full max-w-2xl text-center">
        <h1 className="text-5xl font-semibold text-text-main tracking-tight mb-8">
          Transform Your Resume
        </h1>
        
        <div className="flex h-[48px] rounded-lg shadow-subtle border border-border-subtle overflow-hidden">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.docx"
          />
          <button
            onClick={handleUploadClick}
            className={`flex items-center justify-center px-6 text-sm font-medium transition-colors duration-200 w-48 ${
              fileName
                ? 'bg-primary/90 text-white'
                : 'bg-primary text-white hover:bg-primary/90'
            }`}
          >
            {fileName ? (
              <>
                <CheckIcon className="w-4 h-4 mr-2" />
                <span className="truncate">{fileName}</span>
              </>
            ) : (
              <>
                <UploadIcon className="w-4 h-4 mr-2" />
                <span>Upload Resume</span>
              </>
            )}
          </button>
          <input
            type="text"
            value={jobInput}
            onChange={(e) => setJobInput(e.target.value)}
            placeholder="Paste Job Posting URL or Text..."
            className="flex-1 px-4 bg-surface-light text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        
        <p className="text-xs text-text-main/70 mt-4">
          PDF or DOCX &middot; We'll analyze it against the job description.
        </p>

        <div className="h-10 mt-6">
          <AnimatePresence>
            {isReady && !isLoading && (
                <motion.button
                    onClick={handleContinue}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="bg-accent text-white px-8 py-2 rounded-lg font-medium text-sm hover:bg-accent/90 transition-colors"
                >
                    Continue
                </motion.button>
            )}
            {isLoading && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-sm text-text-main/70"
                >
                    Processing resume...
                </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default InputScreen;
