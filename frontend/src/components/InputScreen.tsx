/**
 * InputScreen Component
 *
 * Main input form for resume optimization.
 * Uses React Hook Form, Zod validation, shadcn components, and full accessibility.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, FileText, Check, Link as LinkIcon, Github, Linkedin, Sparkles, ArrowRight, Zap, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/ui/form-field';
import RecoveryBanner from './shared/RecoveryBanner';
import { stateManager, RecoverySession } from '../services/storage';
import {
  inputScreenSchema,
  type InputScreenFormData,
  isJobUrl,
  normalizeJobInput,
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
    jobTextFromPreview?: string;
  }) => void;
}

export default function InputScreen({ onStart }: InputScreenProps) {
  const prefersReducedMotion = useReducedMotion();

  // File upload state
  const [fileName, setFileName] = useState<string>('');
  const [resumeText, setResumeText] = useState<string>('');
  const [fileError, setFileError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDragActive, setIsDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);

  // UI state
  const [recoverySession, setRecoverySession] = useState<RecoverySession | null>(null);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);
  const [activeIntegrations, setActiveIntegrations] = useState<{ linkedin: boolean; github: boolean }>({
    linkedin: false,
    github: false,
  });

  // Job preview / safety state for job URLs
  const [jobPreviewStatus, setJobPreviewStatus] = useState<'idle' | 'loading' | 'ok' | 'blocked' | 'error'>('idle');
  const [jobPreviewMessage, setJobPreviewMessage] = useState<string>('');
  const [jobPreviewText, setJobPreviewText] = useState<string | null>(null);
  const jobPreviewAbortRef = useRef<AbortController | null>(null);

  // React Hook Form setup
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm<InputScreenFormData>({
    resolver: zodResolver(inputScreenSchema),
    mode: 'onChange',
    reValidateMode: 'onChange',
    defaultValues: {
      jobInput: '',
      linkedinUrl: '',
      githubUsername: '',
      githubToken: '',
    },
  });

  const githubUsername = watch('githubUsername');
  const jobInputValue = watch('jobInput');

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
          
          // Restore active integrations if data exists
          const savedData = session.formData as any;
          if (savedData.linkedinUrl) {
             setValue('linkedinUrl', savedData.linkedinUrl);
             setActiveIntegrations(prev => ({ ...prev, linkedin: true }));
          }
          if (savedData.githubUsername) {
             setValue('githubUsername', savedData.githubUsername);
             setActiveIntegrations(prev => ({ ...prev, github: true }));
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

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set inactive if leaving the dropzone entirely
    if (dropzoneRef.current && !dropzoneRef.current.contains(e.relatedTarget as Node)) {
      setIsDragActive(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setFileError('');

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
  }, []);

  // Job URL preview + safeguard
  useEffect(() => {
    const normalized = normalizeJobInput(jobInputValue || '');

    // Reset when not a URL
    if (!normalized || !isJobUrl(normalized)) {
      setJobPreviewStatus('idle');
      setJobPreviewMessage('');
      setJobPreviewText(null);
      if (jobPreviewAbortRef.current) {
        jobPreviewAbortRef.current.abort();
        jobPreviewAbortRef.current = null;
      }
      return;
    }

    const controller = new AbortController();
    jobPreviewAbortRef.current = controller;

    let cancelled = false;
    setJobPreviewStatus('loading');
    setJobPreviewMessage('Fetching job posting from link...');
    setJobPreviewText(null);

    const fetchPreview = async () => {
      try {
        const { apiClient } = await import('../services/api');
        const response = await apiClient.jobPreview(normalized);
        if (cancelled) return;

        setJobPreviewText(response.job_text);

        if (response.decision === 'BLOCK') {
          setJobPreviewStatus('blocked');
          setJobPreviewMessage(response.reasons[0] || 'Job posting was flagged by safety checks.');
        } else if (response.decision === 'REVIEW') {
          setJobPreviewStatus('error');
          setJobPreviewMessage(response.reasons[0] || 'Job posting may require manual review.');
        } else {
          setJobPreviewStatus('ok');
          setJobPreviewMessage('Job link looks good.');
        }
      } catch (error) {
        if (cancelled) return;
        console.error('Job preview failed:', error);
        setJobPreviewStatus('error');
        setJobPreviewMessage('Could not fetch job posting. You can paste the text instead.');
      }
    };

    fetchPreview();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [jobInputValue]);

  // Form submission
  const onSubmit = (data: InputScreenFormData) => {
    // Defensive check: don't proceed without valid resume text
    if (!resumeText || resumeText.trim().length < 10) {
      setFileError('Please upload a valid resume with sufficient content');
      return;
    }

    const normalizedJobInput = normalizeJobInput(data.jobInput);
    const inputIsUrl = isJobUrl(normalizedJobInput);

    onStart({
      resumeText,
      jobInput: normalizedJobInput,
      isUrl: inputIsUrl,
      linkedinUrl: data.linkedinUrl?.trim() || undefined,
      githubUsername: data.githubUsername?.trim() || undefined,
      githubToken: data.githubToken?.trim() || undefined,
      jobTextFromPreview: inputIsUrl && jobPreviewText ? jobPreviewText : undefined,
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
      setActiveIntegrations({ linkedin: false, github: false });

      console.log('Recovery session cleared');
    } catch (error) {
      console.error('Failed to clear recovery session:', error);
    }
  };

  // Keyboard shortcut: Ctrl/Cmd + V to focus job input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
        const active = document.activeElement as HTMLElement | null;
        const isTypingTarget = !!active && (
          active.tagName === 'INPUT' ||
          active.tagName === 'TEXTAREA' ||
          active.isContentEditable === true
        );
        if (isTypingTarget) return; 

        const jobInput = document.getElementById('job-input') as HTMLElement | null;
        if (jobInput && active !== jobInput) {
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
      initial={prefersReducedMotion ? undefined : "initial"}
      animate={prefersReducedMotion ? undefined : "animate"}
      exit={prefersReducedMotion ? undefined : "exit"}
      className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8 relative overflow-hidden bg-gradient-to-br from-[#FAF9F6] via-[#F5F3EE] to-[#EEF2F1]"
      role="main"
    >
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, hsl(var(--accent)) 1px, transparent 0)`,
        backgroundSize: '40px 40px',
      }} />

      {/* Ambient gradient orbs */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-bl from-accent/10 via-accent/5 to-transparent rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-gradient-to-tr from-amber-100/15 via-orange-50/10 to-transparent rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-3xl relative z-10">
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
        <div className="text-center mb-8 sm:mb-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-semibold uppercase tracking-wider mb-5 shadow-sm">
              <Zap className="w-3.5 h-3.5" />
              <span>AI-Powered Optimizer</span>
            </div>
             
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-text-main tracking-tight mb-5">
              Present Your{' '}
              <span className="relative inline-block">
                <span className="relative z-10 bg-gradient-to-r from-accent via-accent to-accent/80 bg-clip-text text-transparent">
                  Best Self
                </span>
                <motion.span
                  className="absolute -bottom-1 left-0 right-0 h-3 bg-gradient-to-r from-accent/30 via-accent/20 to-accent/30 rounded-full -z-0"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: 0.5, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                />
              </span>
            </h1>
            <p className="text-text-main/60 text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed">
              Upload your resume, connect your profiles, and let our agents tailor your story for any opportunity.
            </p>
          </motion.div>
        </div>

        {/* Main Form Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="bg-white/80 backdrop-blur-xl border border-white/60 shadow-[0_8px_40px_-12px_rgba(0,0,0,0.1)] rounded-3xl p-6 sm:p-8 lg:p-10"
        >
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            
            {/* 1. Holographic 3D Resume Dropzone */}
            <div className="space-y-3">
              <label className="text-sm font-semibold text-text-main/70 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-accent" />
                Resume Source
              </label>
               
              <div 
                ref={dropzoneRef}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="relative [perspective:1000px]"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.doc,image/png,image/jpeg,image/jpg"
                  className="sr-only"
                  id="resume-file-input"
                />
                
                <button
                  type="button"
                  onClick={handleUploadClick}
                  disabled={isLoading}
                  className={cn(
                    'relative w-full min-h-[180px] rounded-2xl overflow-hidden',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:ring-offset-2',
                    'transition-all duration-200',
                    isLoading && 'cursor-wait',
                    !fileName && 'group'
                  )}
                >
                  {/* Clean background */}
                  <div className={cn(
                    'absolute inset-0 transition-all duration-300',
                    fileName 
                      ? 'bg-accent/5'
                      : isDragActive
                        ? 'bg-accent/5'
                        : 'bg-slate-50 group-hover:bg-slate-100/80'
                  )} />
                  
                  {/* Border */}
                  <div className={cn(
                    'absolute inset-0 rounded-2xl transition-all duration-300 pointer-events-none',
                    fileName
                      ? 'border-2 border-accent/40'
                      : isDragActive
                        ? 'border-2 border-accent border-dashed'
                        : 'border-2 border-slate-200 border-dashed group-hover:border-slate-300'
                  )} />

                  {/* Content */}
                  <div className="relative z-10 flex flex-col items-center justify-center min-h-[200px] p-8">
                    <AnimatePresence mode="wait">
                      {isLoading ? (
                        <motion.div 
                          key="loading" 
                          initial={{ opacity: 0, y: 10 }} 
                          animate={{ opacity: 1, y: 0 }} 
                          exit={{ opacity: 0, y: -10 }} 
                          className="flex flex-col items-center gap-5"
                        >
                          <div className="relative">
                            <motion.div 
                              animate={{ rotate: 360 }} 
                              transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }} 
                              className="w-16 h-16 rounded-full border-[3px] border-accent/20 border-t-accent" 
                            />
                            <div className="absolute inset-0 flex items-center justify-center">
                              <FileText className="w-6 h-6 text-accent" />
                            </div>
                          </div>
                          <div className="text-center">
                            <p className="font-semibold text-text-main">Processing Document...</p>
                            <p className="text-sm text-text-main/50 mt-1">Extracting content</p>
                          </div>
                        </motion.div>
                      ) : fileName ? (
                        <motion.div 
                          key="success" 
                          initial={{ opacity: 0, scale: 0.9 }} 
                          animate={{ opacity: 1, scale: 1 }} 
                          exit={{ opacity: 0, scale: 0.9 }} 
                          className="flex flex-col items-center gap-4"
                        >
                          <motion.div 
                            initial={{ scale: 0, rotate: -180 }} 
                            animate={{ scale: 1, rotate: 0 }} 
                            transition={{ type: "spring", stiffness: 200, damping: 15 }} 
                            className="relative"
                          >
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-accent/80 flex items-center justify-center shadow-xl shadow-accent/30">
                              <Check className="w-8 h-8 text-white" strokeWidth={2.5} />
                            </div>
                            <motion.div
                              className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-accent/40 to-accent/30 -z-10"
                              animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0, 0.5] }}
                              transition={{ duration: 2, repeat: Infinity }}
                            />
                          </motion.div>
                          <div className="text-center">
                            <p className="font-bold text-lg text-text-main">{fileName}</p>
                            <p className="text-sm text-accent font-medium mt-1.5 flex items-center gap-1.5 justify-center">
                              <Sparkles className="w-4 h-4" />
                              Ready for optimization
                            </p>
                          </div>
                          <button 
                            type="button" 
                            onClick={(e) => { e.stopPropagation(); setFileName(''); setResumeText(''); }} 
                            className="text-xs text-text-main/40 hover:text-destructive transition-colors flex items-center gap-1.5 mt-2 px-3 py-1.5 rounded-full hover:bg-destructive/5"
                          >
                            <X className="w-3.5 h-3.5" />
                            Remove file
                          </button>
                        </motion.div>
                      ) : (
                        <motion.div 
                          key="empty" 
                          initial={{ opacity: 0 }} 
                          animate={{ opacity: 1 }} 
                          exit={{ opacity: 0 }} 
                          className="flex flex-col items-center gap-5"
                        >
                          <motion.div 
                            animate={isDragActive ? { scale: 1.05, y: -4 } : { scale: 1, y: 0 }} 
                            transition={{ type: "spring", stiffness: 400, damping: 25 }} 
                            className={cn(
                              'w-14 h-14 rounded-xl flex items-center justify-center transition-all duration-300',
                              isDragActive 
                                ? 'bg-accent text-white' 
                                : 'bg-slate-200/60 text-slate-400 group-hover:bg-slate-200 group-hover:text-slate-500'
                            )}
                          >
                            <UploadCloud className="w-7 h-7" />
                          </motion.div>
                          <div className="text-center">
                            <p className={cn(
                              'font-medium text-base transition-colors duration-200',
                              isDragActive ? 'text-accent' : 'text-text-main/70 group-hover:text-text-main'
                            )}>
                              {isDragActive ? 'Release to upload' : 'Drop your resume here'}
                            </p>
                            <p className="text-sm text-text-main/40 mt-1">or click to browse</p>
                          </div>
                          {/* Supported formats hint */}
                          <div className="flex items-center gap-2 text-[11px] text-text-main/30 mt-1">
                            <span className="px-2 py-0.5 rounded bg-slate-100">PDF</span>
                            <span className="px-2 py-0.5 rounded bg-slate-100">DOCX</span>
                            <span className="px-2 py-0.5 rounded bg-slate-100">DOC</span>
                            <span className="px-2 py-0.5 rounded bg-slate-100">Images</span>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </button>
              </div>
              {fileError && (
                <motion.p 
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-destructive font-medium flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-current" />
                  {fileError}
                </motion.p>
              )}
            </div>

            {/* 2. Job Input Field */}
            <div className="space-y-3">
              <label className="text-sm font-semibold text-text-main/70 uppercase tracking-wider flex items-center gap-2">
                <LinkIcon className="w-4 h-4 text-accent" />
                Job Posting
              </label>
              <div className="relative">
                <input
                  {...register('jobInput')}
                  type="text"
                  id="job-input"
                  placeholder="Paste Job URL or Job Description..."
                  className={cn(
                    'w-full h-14 px-5 bg-white border border-slate-200 rounded-xl text-base',
                    'placeholder:text-slate-400',
                    'focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent',
                    'transition-all duration-200 shadow-sm hover:border-slate-300',
                    errors.jobInput && 'border-destructive focus:ring-destructive/20'
                  )}
                />
              </div>
              {/* Validation error */}
              {errors.jobInput && (
                <p className="text-xs text-destructive font-medium pl-1">
                  {errors.jobInput.message}
                </p>
              )}
              {/* Job Preview Status */}
              <AnimatePresence>
                {jobPreviewStatus !== 'idle' && !errors.jobInput && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className={cn(
                      'text-xs font-medium pl-1',
                      jobPreviewStatus === 'ok' && 'text-emerald-600',
                      jobPreviewStatus === 'error' && 'text-amber-600',
                      jobPreviewStatus === 'blocked' && 'text-destructive',
                      jobPreviewStatus === 'loading' && 'text-slate-500'
                    )}
                  >
                    {jobPreviewMessage}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 3. Integrations Grid */}
            <div className="space-y-4">
              <label className="text-sm font-semibold text-text-main/70 uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent" />
                Profile Integrations
              </label>
               
              <div className="grid sm:grid-cols-2 gap-4">
                {/* LinkedIn Card */}
                <motion.div 
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className={cn(
                    'border rounded-xl p-4 transition-all duration-200 cursor-pointer',
                    activeIntegrations.linkedin 
                      ? 'bg-sky-50/80 border-sky-200 ring-1 ring-sky-200/50' 
                      : 'bg-white border-slate-200 hover:border-sky-300 hover:bg-sky-50/30'
                  )}
                  onClick={() => {
                    if (!activeIntegrations.linkedin) setActiveIntegrations(p => ({...p, linkedin: true}));
                  }}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#0077b5] to-[#0066a0] text-white flex items-center justify-center shadow-md shadow-sky-500/20">
                      <Linkedin className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-text-main">LinkedIn</p>
                      <p className="text-[10px] text-text-main/50">Professional History</p>
                    </div>
                    {activeIntegrations.linkedin && (
                      <button 
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveIntegrations(p => ({...p, linkedin: false}));
                          setValue('linkedinUrl', '');
                        }}
                        className="w-6 h-6 rounded-full bg-slate-100 hover:bg-destructive/10 text-slate-400 hover:text-destructive flex items-center justify-center transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                   
                  {activeIntegrations.linkedin ? (
                    <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} className="space-y-1">
                      <input 
                        {...register('linkedinUrl')}
                        type="url" 
                        placeholder="https://linkedin.com/in/yourprofile" 
                        className={cn(
                          "w-full bg-white text-sm px-3 py-2.5 rounded-lg border focus:ring-1 focus:outline-none transition-all",
                          errors.linkedinUrl ? "border-destructive focus:border-destructive focus:ring-destructive/20" : "border-slate-200 focus:border-sky-400 focus:ring-sky-400/20"
                        )}
                        onClick={(e) => e.stopPropagation()}
                        autoFocus
                      />
                      {errors.linkedinUrl && (
                        <p className="text-[10px] text-destructive">{errors.linkedinUrl.message}</p>
                      )}
                    </motion.div>
                  ) : (
                    <p className="text-xs text-text-main/40 pl-1">Connect to analyze work history & skills</p>
                  )}
                </motion.div>

                {/* GitHub Card */}
                <motion.div 
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className={cn(
                    'border rounded-xl p-4 transition-all duration-200 cursor-pointer',
                    activeIntegrations.github 
                      ? 'bg-slate-50/80 border-slate-300 ring-1 ring-slate-300/50' 
                      : 'bg-white border-slate-200 hover:border-slate-400 hover:bg-slate-50/30'
                  )}
                  onClick={() => {
                    if (!activeIntegrations.github) setActiveIntegrations(p => ({...p, github: true}));
                  }}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#24292e] to-[#1a1e22] text-white flex items-center justify-center shadow-md shadow-slate-500/20">
                      <Github className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-text-main">GitHub</p>
                      <p className="text-[10px] text-text-main/50">Code Quality</p>
                    </div>
                    {activeIntegrations.github && (
                      <button 
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveIntegrations(p => ({...p, github: false}));
                          setValue('githubUsername', '');
                          setValue('githubToken', '');
                        }}
                        className="w-6 h-6 rounded-full bg-slate-100 hover:bg-destructive/10 text-slate-400 hover:text-destructive flex items-center justify-center transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                   
                  {activeIntegrations.github ? (
                    <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
                      <div>
                        <input 
                          {...register('githubUsername')}
                          type="text" 
                          placeholder="Username" 
                          className={cn(
                            "w-full bg-white text-sm px-3 py-2.5 rounded-lg border focus:ring-1 focus:outline-none transition-all",
                            errors.githubUsername ? "border-destructive focus:border-destructive focus:ring-destructive/20" : "border-slate-200 focus:border-slate-400 focus:ring-slate-400/20"
                          )}
                          onClick={(e) => e.stopPropagation()}
                          autoFocus
                        />
                        {errors.githubUsername && (
                          <p className="text-[10px] text-destructive mt-1">{errors.githubUsername.message}</p>
                        )}
                      </div>
                      <div>
                        <input 
                          {...register('githubToken')}
                          type="password" 
                          placeholder="Token (Optional)" 
                          className={cn(
                            "w-full bg-white text-xs px-3 py-2 rounded-lg border focus:ring-1 focus:outline-none transition-all",
                            errors.githubToken ? "border-destructive focus:border-destructive focus:ring-destructive/20" : "border-slate-200 focus:border-slate-400 focus:ring-slate-400/20"
                          )}
                          onClick={(e) => e.stopPropagation()}
                        />
                        {errors.githubToken && (
                          <p className="text-[10px] text-destructive mt-1">{errors.githubToken.message}</p>
                        )}
                      </div>
                    </motion.div>
                  ) : (
                    <p className="text-xs text-text-main/40 pl-1">Analyze repos & technical stack</p>
                  )}
                </motion.div>
              </div>
            </div>

            {/* Submit Action */}
            <div className="pt-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Button
                  type="submit"
                  size="lg"
                  disabled={!isReady || isLoading}
                  className={cn(
                    "w-full h-14 text-base font-semibold rounded-xl transition-all duration-300 group",
                    isReady 
                      ? "bg-accent text-white shadow-lg shadow-accent/25 hover:shadow-accent/40 hover:-translate-y-0.5 hover:bg-accent/90" 
                      : "bg-slate-100 text-slate-400 border border-slate-200 shadow-none cursor-not-allowed"
                  )}
                >
                  <span className="flex items-center justify-center gap-2">
                    {isLoading ? 'Analyzing...' : 'Initialize Optimization Agent'}
                    {isReady && !isLoading && <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />}
                  </span>
                </Button>
              </motion.div>
              
              <p className="text-center text-xs text-text-main/40 mt-5">
                By continuing, you agree to our secure data processing terms.
              </p>
            </div>

          </form>
        </motion.div>
      </div>
    </motion.div>
  );
}
