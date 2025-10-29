
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadIcon, CheckIcon, LinkedInIcon, GitHubIcon } from './icons';

interface InputScreenProps {
  onStart: (data: { 
    resumeText: string; 
    jobInput: string; 
    isUrl: boolean;
    linkedinUrl?: string;
    githubUsername?: string;
    githubToken?: string;
  }) => void;
}

const InputScreen: React.FC<InputScreenProps> = ({ onStart }) => {
  const [fileName, setFileName] = useState<string>('');
  const [resumeText, setResumeText] = useState<string>('');
  const [jobInput, setJobInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [linkedinUrl, setLinkedinUrl] = useState<string>('');
  const [githubUsername, setGithubUsername] = useState<string>('');  const [githubToken, setGithubToken] = useState<string>('');
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
      onStart({ 
        resumeText, 
        jobInput, 
        isUrl,
        linkedinUrl: linkedinUrl.trim() || undefined,
        githubUsername: githubUsername.trim() || undefined,
        githubToken: githubToken.trim() || undefined,
      });
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
            disabled={isLoading}
            className={`flex items-center justify-center px-6 text-sm font-medium transition-colors duration-200 w-48 ${
              isLoading
                ? 'bg-primary/70 text-white cursor-wait'
                : fileName
                ? 'bg-primary/90 text-white'
                : 'bg-primary text-white hover:bg-primary/90'
            }`}
          >
            {isLoading ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full"
                />
                <span>Processing...</span>
              </>
            ) : fileName ? (
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
          PDF or DOCX • We'll analyze it against the job description.
        </p>

        {/* Optional Enhancements Toggle */}
        <div className="mt-6">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-primary hover:text-primary/80 transition-colors font-medium flex items-center gap-2 mx-auto"
          >
            <span>{showAdvanced ? '−' : '+'}</span>
            <span>Optional Enhancements</span>
          </button>
        </div>

        {/* Expandable Optional Enhancements */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0, marginTop: 0 }}
              animate={{ opacity: 1, height: 'auto', marginTop: 16 }}
              exit={{ opacity: 0, height: 0, marginTop: 0 }}
              transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
              className="overflow-hidden"
            >
              <div className="bg-gradient-to-br from-surface-light to-white rounded-xl border border-border-subtle shadow-lg p-8 space-y-6">
                {/* LinkedIn Input */}
                <div className="group">
                  <label className="flex items-center gap-2 text-sm font-semibold text-text-main mb-3">
                    <LinkedInIcon className="w-5 h-5 text-primary" />
                    <span>LinkedIn Profile</span>
                    <span className="text-text-main/40 font-normal text-xs">(optional)</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={linkedinUrl}
                      onChange={(e) => setLinkedinUrl(e.target.value)}
                      placeholder="https://linkedin.com/in/yourname"
                      className="w-full px-4 py-3 bg-white border border-border-subtle rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all duration-200 shadow-sm hover:shadow-md"
                    />
                  </div>
                  <p className="text-xs text-text-main/60 mt-2 leading-relaxed">
                    Build a rich profile index for enhanced personalization across applications
                  </p>
                </div>

                {/* Divider */}
                <div className="border-t border-border-subtle/50"></div>

                {/* GitHub Input */}
                <div className="group">
                  <label className="flex items-center gap-2 text-sm font-semibold text-text-main mb-3">
                    <GitHubIcon className="w-5 h-5 text-text-main/70" />
                    <span>GitHub Username</span>
                    <span className="text-text-main/40 font-normal text-xs">(optional)</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={githubUsername}
                      onChange={(e) => setGithubUsername(e.target.value)}
                      placeholder="yourusername"
                      className="w-full px-4 py-3 bg-white border border-border-subtle rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all duration-200 shadow-sm hover:shadow-md"
                    />
                  </div>
                  <p className="text-xs text-text-main/60 mt-2 leading-relaxed">
                    Showcase your open-source contributions and technical projects
                  </p>
                  
                  {/* GitHub Token - only show if username is entered */}
                  {githubUsername && (
                    <div className="mt-3 pt-3 border-t border-border-subtle/30">
                      <label className="block text-xs font-medium text-text-main/70 mb-2">
                        GitHub Token (optional, for private repos & higher rate limits)
                      </label>
                      <input
                        type="password"
                        value={githubToken}
                        onChange={(e) => setGithubToken(e.target.value)}
                        placeholder="ghp_••••••••••••••••••••"
                        className="w-full px-3 py-2 bg-white border border-border-subtle rounded text-xs placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all duration-200"
                      />
                      <div className="mt-1.5 space-y-1">
                        <p className="text-xs text-text-main/50">
                          <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                            Create token
                          </a> • Only stored for this session
                        </p>
                        <p className="text-xs text-text-main/50">
                          💡 Required scopes: <code className="text-xs bg-surface-light px-1 py-0.5 rounded">public_repo</code> or <code className="text-xs bg-surface-light px-1 py-0.5 rounded">repo</code> (for private repos)
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

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
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default InputScreen;
