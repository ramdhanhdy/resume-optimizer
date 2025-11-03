/**
 * InputScreen Component
 *
 * Main input form for resume optimization.
 * Uses React Hook Form, Zod validation, shadcn components, and full accessibility.
 */

import { useState, useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadIcon, CheckIcon, LinkedInIcon, GitHubIcon } from './icons';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/ui/form-field';
import RecoveryBanner from './shared/RecoveryBanner';
import { stateManager, RecoverySession } from '../services/storage';
import {
  inputScreenSchema,
  type InputScreenFormData,
  isJobUrl,
  validateResumeFile,
} from '@/design-system/forms/schemas/input-screen-schema';
import { slideUpVariants, fadeVariants, useReducedMotion } from '@/design-system/animations';
import { cn } from '@/lib/utils';

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

export default function InputScreen({ onStart }: InputScreenProps) {
  const prefersReducedMotion = useReducedMotion();

  // File upload state
  const [fileName, setFileName] = useState<string>('');
  const [resumeText, setResumeText] = useState<string>('');
  const [fileError, setFileError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // UI state
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [recoverySession, setRecoverySession] = useState<RecoverySession | null>(null);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);

  // React Hook Form setup
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm<InputScreenFormData>({
    resolver: zodResolver(inputScreenSchema),
    mode: 'onBlur',
    defaultValues: {
      jobInput: '',
      linkedinUrl: '',
      githubUsername: '',
      githubToken: '',
    },
  });

  const githubUsername = watch('githubUsername');

  // Check for recovery session on mount
  useEffect(() => {
    const checkRecovery = async () => {
      try {
        const session = await stateManager.findLatestSession();
        if (session) {
          console.log('Found recovery session:', session.sessionId);
          setRecoverySession(session);

          // Restore form data
          if (session.formData.jobPosting) {
            setValue('jobInput', session.formData.jobPosting);
          }

          // Restore file
          if (session.fileMetadata) {
            const file = await stateManager.loadFile(session.sessionId);
            if (file) {
              setFileName(file.name);
              // Upload file to get text
              setIsLoading(true);
              try {
                const { apiClient } = await import('../services/api');
                const response = await apiClient.uploadResume(file);
                setResumeText(response.text);
              } catch (error) {
                console.error('Failed to restore file:', error);
                setFileError('Failed to restore file from recovery session');
              } finally {
                setIsLoading(false);
              }
            }
          }
        }
      } catch (error) {
        console.error('Failed to check recovery:', error);
      }
    };

    checkRecovery();
  }, [setValue]);

  // File upload handler
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setFileError('');

    // Client-side validation
    const validation = validateResumeFile(file);
    if (!validation.isValid) {
      setFileError(validation.error || 'Invalid file');
      setFileName('');
      setResumeText('');
      return;
    }

    setFileName(file.name);
    setIsLoading(true);

    try {
      const { apiClient } = await import('../services/api');
      const response = await apiClient.uploadResume(file);
      setResumeText(response.text);
      setFileError('');
    } catch (error) {
      console.error('Failed to upload resume:', error);
      setFileError('Failed to upload resume. Please try again.');
      setFileName('');
      setResumeText('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // Form submission
  const onSubmit = (data: InputScreenFormData) => {
    // Defensive check: don't proceed without valid resume text
    if (!resumeText || resumeText.trim().length < 10) {
      setFileError('Please upload a valid resume with sufficient content');
      return;
    }

    onStart({
      resumeText,
      jobInput: data.jobInput,
      isUrl: isJobUrl(data.jobInput),
      linkedinUrl: data.linkedinUrl?.trim() || undefined,
      githubUsername: data.githubUsername?.trim() || undefined,
      githubToken: data.githubToken?.trim() || undefined,
    });
  };

  // Recovery handlers
  const handleRetry = async () => {
    if (!recoverySession) return;

    setIsRetrying(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/optimize-retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId: recoverySession.sessionId,
          formData: recoverySession.formData,
        }),
      });

      if (!response.ok) {
        throw new Error('Retry request failed');
      }

      const result = await response.json();
      console.log('Retry initiated:', result);

      // Proceed with normal flow
      handleSubmit(onSubmit)();
    } catch (error) {
      console.error('Retry failed:', error);
      setFileError('Failed to retry. Please try again or start fresh.');
    } finally {
      setIsRetrying(false);
    }
  };

  const handleStartFresh = async () => {
    if (!recoverySession) return;

    const confirmed = window.confirm(
      'This will discard your preserved data. Are you sure you want to start fresh?'
    );

    if (!confirmed) return;

    try {
      await stateManager.cleanupSession(recoverySession.sessionId);
      setRecoverySession(null);

      // Reset form
      setFileName('');
      setResumeText('');
      setFileError('');
      setValue('jobInput', '');
      setValue('linkedinUrl', '');
      setValue('githubUsername', '');
      setValue('githubToken', '');

      console.log('Recovery session cleared');
    } catch (error) {
      console.error('Failed to clear recovery session:', error);
    }
  };

  // Keyboard shortcut: Ctrl/Cmd + V to focus job input (for pasting)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
        // Let browser handle paste, but ensure focus
        const jobInput = document.getElementById('job-input');
        if (jobInput && document.activeElement !== jobInput) {
          e.preventDefault();
          jobInput.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const isReady = !!fileName && isValid && !!resumeText;

  return (
    <motion.div
      variants={prefersReducedMotion ? undefined : slideUpVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="min-h-screen flex items-center justify-center p-4 sm:p-8"
      role="main"
      aria-label="Resume optimization form"
    >
      <div className="w-full max-w-2xl">
        {/* Recovery Banner */}
        <AnimatePresence>
          {recoverySession && (
            <RecoveryBanner
              session={recoverySession}
              onRetry={handleRetry}
              onStartFresh={handleStartFresh}
              isRetrying={isRetrying}
            />
          )}
        </AnimatePresence>

        {/* Header */}
        <div className="text-center mb-8">
          <motion.h1
            variants={prefersReducedMotion ? undefined : fadeVariants}
            initial="initial"
            animate="animate"
            className="text-4xl sm:text-5xl font-semibold text-foreground tracking-tight"
          >
            Transform Your Resume
          </motion.h1>
          <p className="text-sm text-muted-foreground mt-2">
            Upload your resume and paste the job posting to get started
          </p>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* File Upload + Job Input Row */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-0">
            {/* File Upload Button */}
            <div className="sm:w-48 flex-shrink-0">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.docx,.doc,image/png,image/jpeg,image/jpg"
                className="sr-only"
                id="resume-file-input"
                aria-describedby={fileError ? 'file-error' : 'file-helper'}
                aria-invalid={!!fileError}
              />
              <Button
                type="button"
                onClick={handleUploadClick}
                disabled={isLoading}
                className={cn(
                  'w-full h-12 sm:h-[48px] sm:rounded-r-none text-sm font-medium transition-colors duration-200 text-white',
                  isLoading && 'cursor-wait',
                  fileName && !fileError && 'bg-primary/90'
                )}
                aria-label={
                  fileName
                    ? `Resume uploaded: ${fileName}. Click to upload a different file.`
                    : 'Upload resume file'
                }
              >
                {isLoading ? (
                  <>
                    <motion.div
                      animate={{ rotate: prefersReducedMotion ? 0 : 360 }}
                      transition={{
                        duration: prefersReducedMotion ? 0 : 1,
                        repeat: prefersReducedMotion ? 0 : Infinity,
                        ease: 'linear',
                      }}
                      className="w-4 h-4 mr-2 border-2 border-current border-t-transparent rounded-full"
                      aria-hidden="true"
                    />
                    <span>Processing...</span>
                  </>
                ) : fileName ? (
                  <>
                    <CheckIcon className="w-4 h-4 mr-2" aria-hidden="true" />
                    <span className="truncate">{fileName}</span>
                  </>
                ) : (
                  <>
                    <UploadIcon className="w-4 h-4 mr-2" aria-hidden="true" />
                    <span>Upload Resume</span>
                  </>
                )}
              </Button>
            </div>

            {/* Job Input Field */}
            <div className="flex-1">
              <input
                {...register('jobInput')}
                type="text"
                id="job-input"
                placeholder="Paste Job Posting URL or Text..."
                className={cn(
                  'w-full h-12 sm:h-[48px] px-4 bg-background border-2 border-primary rounded-lg sm:rounded-l-none text-sm',
                  'placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
                  'transition-all duration-200 shadow-sm hover:shadow-md',
                  errors.jobInput &&
                    'border-destructive focus:ring-destructive'
                )}
                aria-label="Job posting URL or text"
                aria-invalid={!!errors.jobInput}
                aria-describedby={errors.jobInput ? 'job-input-error' : undefined}
              />
            </div>
          </div>

          {/* File Error */}
          {fileError && (
            <div
              id="file-error"
              className="text-sm text-destructive font-medium flex items-center justify-center gap-2"
              role="alert"
              aria-live="polite"
            >
              <span className="flex-shrink-0">⚠️</span>
              <span>{fileError}</span>
            </div>
          )}



          {/* Helper Text */}
          {!fileError && (
            <p id="file-helper" className="text-xs text-muted-foreground text-center">
              PDF or DOCX • We'll analyze it against the job description
            </p>
          )}

          {/* Optional Enhancements Toggle */}
          <div className="text-center">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm font-medium text-primary hover:text-primary/80"
              aria-expanded={showAdvanced}
              aria-controls="advanced-options"
              aria-label={
                showAdvanced
                  ? 'Hide optional enhancements'
                  : 'Show optional enhancements'
              }
            >
              <span className="mr-2">{showAdvanced ? '−' : '+'}</span>
              <span>Optional Enhancements</span>
            </Button>
          </div>

          {/* Expandable Optional Enhancements */}
          <AnimatePresence>
            {showAdvanced && (
              <motion.div
                id="advanced-options"
                initial={{ opacity: 0, height: 0, marginTop: 0 }}
                animate={{ opacity: 1, height: 'auto', marginTop: 16 }}
                exit={{ opacity: 0, height: 0, marginTop: 0 }}
                transition={{
                  duration: prefersReducedMotion ? 0 : 0.3,
                  ease: [0.4, 0.0, 0.2, 1],
                }}
                className="overflow-hidden"
                role="region"
                aria-label="Optional enhancement fields"
              >
                <div className="bg-gradient-to-br from-muted/30 to-background rounded-xl border border-border shadow-lg p-6 sm:p-8 space-y-6">
                  {/* LinkedIn Input */}
                  <FormField
                    {...register('linkedinUrl')}
                    type="url"
                    label="LinkedIn Profile"
                    placeholder="https://linkedin.com/in/yourname"
                    icon={<LinkedInIcon className="w-5 h-5 text-primary" />}
                    error={errors.linkedinUrl?.message}
                    helperText="Build a rich profile index for enhanced personalization across applications"
                    containerClassName="group"
                  />

                  {/* Divider */}
                  <div className="border-t border-border" role="separator" />

                  {/* GitHub Username */}
                  <FormField
                    {...register('githubUsername')}
                    type="text"
                    label="GitHub Username"
                    placeholder="yourusername"
                    icon={
                      <GitHubIcon className="w-5 h-5 text-muted-foreground" />
                    }
                    error={errors.githubUsername?.message}
                    helperText="Showcase your open-source contributions and technical projects"
                    containerClassName="group"
                  />

                  {/* GitHub Token - only show if username is entered */}
                  <AnimatePresence>
                    {githubUsername && githubUsername.trim() !== '' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{
                          duration: prefersReducedMotion ? 0 : 0.2,
                        }}
                        className="pt-3 border-t border-border/30"
                      >
                        <FormField
                          {...register('githubToken')}
                          type="password"
                          label="GitHub Token"
                          placeholder="ghp_••••••••••••••••••••"
                          error={errors.githubToken?.message}
                          helperText={
                            <span>
                              <a
                                href="https://github.com/settings/tokens"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline"
                              >
                                Create token
                              </a>{' '}
                              • Only stored for this session • Required scopes:{' '}
                              <code className="bg-muted px-1 py-0.5 rounded text-xs">
                                public_repo
                              </code>{' '}
                              or{' '}
                              <code className="bg-muted px-1 py-0.5 rounded text-xs">
                                repo
                              </code>
                            </span>
                          }
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Submit Button */}
          <div className="flex justify-center pt-4">
            <AnimatePresence mode="wait">
              {isReady && !isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{
                    duration: prefersReducedMotion ? 0 : 0.2,
                  }}
                >
                  <Button
                    type="submit"
                    size="lg"
                    className="bg-accent text-white hover:bg-accent/90 px-8"
                    aria-label="Continue to resume optimization"
                  >
                    Continue
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </form>


      </div>
    </motion.div>
  );
}
