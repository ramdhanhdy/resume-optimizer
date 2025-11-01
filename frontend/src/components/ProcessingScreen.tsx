
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PROCESSING_ACTIVITIES, PROCESSING_PHASES, MOCK_INSIGHTS } from '../constants';
import type { Insight } from '../types';
import { useProcessingJob } from '../hooks/useProcessingJob';
import { apiClient } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ProcessingScreenProps {
  onComplete: (appState: any) => void;
  resumeText: string;
  jobText?: string;
  jobUrl?: string;
  linkedinUrl?: string;
  githubUsername?: string;
  githubToken?: string;
}

const TOTAL_DURATION = 12000; // 12 seconds estimate

// Feature flag for streaming (set to true to use new streaming infrastructure)
const USE_STREAMING = true;

const ProcessingScreen: React.FC<ProcessingScreenProps> = ({ onComplete, resumeText, jobText, jobUrl, linkedinUrl, githubUsername, githubToken }) => {
  const [currentActivity, setCurrentActivity] = useState(PROCESSING_ACTIVITIES[0]);
  const [currentPhase, setCurrentPhase] = useState(PROCESSING_PHASES[0]);
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const hasStartedRef = React.useRef(false);
  
  // Simplified insight display - just track by ID
  const [insights, setInsights] = useState<Insight[]>([]);
  const seenInsightIds = React.useRef<Set<string>>(new Set());

  // Reset on new job
  useEffect(() => {
    if (jobId) {
      seenInsightIds.current.clear();
      setInsights([]);
    }
  }, [jobId]);
  
  // Use streaming hook
  const { state: streamState, isComplete, isFailed } = useProcessingJob(jobId);

  useEffect(() => {
    // Prevent duplicate pipeline runs (React StrictMode double-mount protection)
    if (hasStartedRef.current) {
      console.log('⏭️ Pipeline already started, skipping duplicate run');
      return;
    }
    hasStartedRef.current = true;

    let cancelled = false;
    let progressInterval: NodeJS.Timeout;
    let activityInterval: NodeJS.Timeout;
    let phaseInterval: NodeJS.Timeout;
    let insightInterval: NodeJS.Timeout;

    const runPipeline = async () => {
      console.log('🚀 Starting pipeline with:', { resumeText: resumeText.substring(0, 50) + '...', jobText, jobUrl });
      
      // NEW: Use streaming pipeline if enabled
      if (USE_STREAMING) {
        try {
          console.log('📡 Starting streaming pipeline...');
          const response = await apiClient.startPipeline({
            resume_text: resumeText,
            job_text: jobText,
            job_url: jobUrl,
            linkedin_url: linkedinUrl,
            github_username: githubUsername,
            github_token: githubToken,
          });
          
          console.log('✅ Pipeline started with job_id:', response.job_id);
          setJobId(response.job_id);
          
          // The streaming hook will handle the rest
          return;
        } catch (error) {
          console.error('❌ Failed to start streaming pipeline:', error);
          alert(`Failed to start pipeline: ${error instanceof Error ? error.message : 'Unknown error'}`);
          return;
        }
      }
      
      try {
        const { apiClient } = await import('../services/api');

        // Agent 1: Analyze Job
        console.log('📋 Agent 1: Analyzing job...');
        setCurrentPhase(PROCESSING_PHASES[0]);
        setCurrentActivity(PROCESSING_ACTIVITIES[0]);
        
        const jobAnalysis = await apiClient.analyzeJob({
          job_text: jobText,
          job_url: jobUrl,
        });
        console.log('✓ Agent 1 complete:', jobAnalysis);

        // Agent 2: Optimize Resume
        console.log('📋 Agent 2: Optimizing resume...');
        setCurrentPhase(PROCESSING_PHASES[1]);
        setProgress(25);
        
        const optimization = await apiClient.optimizeResume({
          application_id: jobAnalysis.application_id,
          resume_text: resumeText,
        });
        console.log('✓ Agent 2 complete:', optimization);

        // Agent 3: Implement
        console.log('📋 Agent 3: Implementing optimizations...');
        setCurrentPhase(PROCESSING_PHASES[2]);
        setProgress(50);
        
        const implementation = await apiClient.implementOptimization(
          jobAnalysis.application_id
        );
        console.log('✓ Agent 3 complete:', implementation);

        // Agent 4: Validate
        console.log('📋 Agent 4: Validating resume...');
        setCurrentPhase(PROCESSING_PHASES[3]);
        setProgress(75);
        
        const validation = await apiClient.validateResume(
          jobAnalysis.application_id
        );
        console.log('✓ Agent 4 complete:', validation);

        // Agent 5: Polish
        console.log('📋 Agent 5: Polishing resume...');
        setCurrentPhase(PROCESSING_PHASES[4]);
        setProgress(90);
        
        const polish = await apiClient.polishResume({
          application_id: jobAnalysis.application_id,
        });
        console.log('✓ Agent 5 complete:', polish);

        setProgress(100);
        
        // Clear all mock timers before transitioning
        console.log('🧹 Clearing all animation timers...');
        clearInterval(progressInterval);
        clearInterval(activityInterval);
        clearInterval(phaseInterval);
        clearInterval(insightInterval);
        
        // Complete with application state
        const completionData = {
          applicationId: jobAnalysis.application_id,
          companyName: jobAnalysis.company_name,
          jobTitle: jobAnalysis.job_title,
          validationScores: validation.scores,
        };
        
        console.log('✨ All agents complete! Calling onComplete with:', completionData);
        
        setTimeout(() => {
          if (!cancelled) {
            console.log('🎯 Executing onComplete callback...');
            onComplete(completionData);
          } else {
            console.log('⚠️ Component unmounted, but pipeline completed successfully. Skipping onComplete.');
          }
        }, 500);

      } catch (error) {
        console.error('❌ Pipeline failed:', error);
        if (!cancelled) {
          alert(`Processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }
    };

    runPipeline();

    // Overall progress and completion timer (fallback)
    progressInterval = setInterval(() => {
      setProgress(p => {
        const newProgress = Math.min(p + 1, 95); // Cap at 95% until real completion
        return newProgress;
      });
    }, 100);

    // Activity text cycling
    let activityIndex = 0;
    activityInterval = setInterval(() => {
      activityIndex = (activityIndex + 1) % PROCESSING_ACTIVITIES.length;
      setCurrentActivity(PROCESSING_ACTIVITIES[activityIndex]);
    }, TOTAL_DURATION / PROCESSING_ACTIVITIES.length);

    // Phase text cycling
    let phaseIndex = 0;
    phaseInterval = setInterval(() => {
        phaseIndex = (phaseIndex + 1) % PROCESSING_PHASES.length;
        setCurrentPhase(PROCESSING_PHASES[phaseIndex]);
    }, TOTAL_DURATION / PROCESSING_PHASES.length);


    // Insight card stacking
    let insightIndex = 0;
    insightInterval = setInterval(() => {
      if (insightIndex < MOCK_INSIGHTS.length) {
        setInsights(currentInsights => [MOCK_INSIGHTS[insightIndex], ...currentInsights].slice(0, 4));
        insightIndex++;
      } else {
        clearInterval(insightInterval);
      }
    }, TOTAL_DURATION / (MOCK_INSIGHTS.length + 1));

    return () => {
      console.log('🛑 Component unmounting, cleaning up timers (pipeline continues)...');
      cancelled = true;  // Only prevents onComplete callback
      clearInterval(progressInterval);
      clearInterval(activityInterval);
      clearInterval(phaseInterval);
      clearInterval(insightInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeText, jobText, jobUrl]);

  // Sync streaming state to UI state
  useEffect(() => {
    if (!streamState || !USE_STREAMING) return;

    // Update phase based on current step
    if (streamState.currentStep) {
      const stepToPhaseMap: Record<string, string> = {
        'analyzing': PROCESSING_PHASES[0],
        'planning': PROCESSING_PHASES[1],
        'writing': PROCESSING_PHASES[2],
        'validating': PROCESSING_PHASES[3],
        'polishing': PROCESSING_PHASES[4],
      };
      
      const newPhase = stepToPhaseMap[streamState.currentStep];
      if (newPhase) {
        setCurrentPhase(newPhase);
      }
    }

    // Update center activity text from system insights (category: "system")
    const systemInsights = streamState.insights.filter(ins => ins.category === 'system');
    if (systemInsights.length > 0) {
      // Show the most recent system message in the center
      const latestSystem = systemInsights[0];
      setCurrentActivity(latestSystem.message);
    }

    // Update insights from stream - ONLY non-system insights (actual LLM insights)
    const actualInsights = streamState.insights.filter(ins => ins.category !== 'system');
    
    // Find new insights we haven't seen yet
    const newInsights = actualInsights.filter(ins => !seenInsightIds.current.has(ins.id));
    
    if (newInsights.length > 0) {
      console.log(`📊 Adding ${newInsights.length} new insights`);
      
      // Mark as seen
      newInsights.forEach(ins => seenInsightIds.current.add(ins.id));
      
      // Add to display list (keep last 10)
      setInsights(prev => {
        const updated = [
          ...newInsights.map(ins => ({
            id: ins.id,
            text: ins.message,
            category: ins.category,
          })),
          ...prev,
        ];
        return updated.slice(0, 10); // Keep last 10 insights
      });
    }

    // Calculate overall progress from steps
    const completedSteps = streamState.steps.filter(s => s.status === 'completed').length;
    const inProgressStep = streamState.steps.find(s => s.status === 'in_progress');
    const stepProgress = inProgressStep ? inProgressStep.progress / 100 : 0;
    const overallProgress = ((completedSteps + stepProgress) / streamState.steps.length) * 100;
    setProgress(Math.min(overallProgress, 100));

  }, [streamState]);

  // Handle streaming completion
  useEffect(() => {
    if (!USE_STREAMING || !isComplete || !streamState) return;

    console.log('✨ Streaming pipeline complete!');
    
    const handleCompletion = async () => {
      // Extract application data from metrics
      let applicationId = streamState.metrics['application_id']?.value;
      
      // Fallback: fetch from snapshot if application_id is missing
      if (!applicationId && jobId) {
        console.log('⚠️ application_id not in metrics, fetching from snapshot...');
        try {
          const { apiClient } = await import('../services/api');
          const snapshot = await apiClient.getJobSnapshot(jobId);
          applicationId = snapshot.metrics?.application_id?.value;
          console.log('✅ Retrieved application_id from snapshot:', applicationId);
        } catch (error) {
          console.error('❌ Failed to fetch application_id from snapshot:', error);
        }
      }
      
      if (!applicationId) {
        console.error('❌ Could not retrieve application_id');
        alert('Pipeline completed but application ID is missing. Please check the console.');
        return;
      }
      
      const overallScore = streamState.metrics['overall_score']?.value || 87;
      const requirementsMatch = streamState.metrics['requirements_match']?.value || 90;
      const atsOptimization = streamState.metrics['ats_optimization']?.value || 85;
      const culturalFit = streamState.metrics['cultural_fit']?.value || 86;

      const completionData = {
        applicationId,
        companyName: 'Company', // TODO: Extract from analysis
        jobTitle: 'Position', // TODO: Extract from analysis
        validationScores: {
          overall: overallScore,
          requirements_match: requirementsMatch,
          ats_optimization: atsOptimization,
          cultural_fit: culturalFit,
        },
      };

      console.log('🎯 Calling onComplete with:', completionData);
      onComplete(completionData);
    };

    setTimeout(() => {
      handleCompletion();
    }, 500);

  }, [isComplete, streamState, onComplete, jobId]);

  // Handle streaming failure
  useEffect(() => {
    if (!USE_STREAMING || !isFailed) return;
    
    console.error('❌ Streaming pipeline failed');
    alert('Pipeline failed. Please try again.');
  }, [isFailed]);

  // Define phases for progress visualization
  const phases = [
    { key: 'analyzing', label: 'Analyzing requirements', step: 'analyzing' },
    { key: 'planning', label: 'Planning optimization', step: 'planning' },
    { key: 'writing', label: 'Crafting resume', step: 'writing' },
    { key: 'validating', label: 'Quality check', step: 'validating' },
    { key: 'polishing', label: 'Final polish', step: 'polishing' },
  ];

  // Determine current phase index based on streamState
  const getCurrentPhaseIndex = () => {
    if (!streamState?.currentStep) return 0;
    const index = phases.findIndex(p => p.step === streamState.currentStep);
    return index >= 0 ? index : 0;
  };

  const currentPhaseIndex = getCurrentPhaseIndex();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
      className="min-h-screen flex flex-col items-center justify-center px-12 py-16 relative overflow-hidden"
    >
      {/* Phase Progress Bar - Top */}
      <div className="absolute top-12 left-0 right-0 px-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between gap-2">
            {phases.map((phase, index) => {
              const isComplete = index < currentPhaseIndex;
              const isCurrent = index === currentPhaseIndex;
              const isFuture = index > currentPhaseIndex;
              
              return (
                <React.Fragment key={phase.key}>
                  {/* Phase Step */}
                  <div className="flex flex-col items-center gap-2 flex-1">
                    <motion.div
                      className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                        isComplete
                          ? 'bg-accent border-accent'
                          : isCurrent
                          ? 'bg-accent/20 border-accent animate-pulse'
                          : 'bg-surface-light border-border-subtle'
                      }`}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      {isComplete ? (
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span className={`text-sm font-semibold ${
                          isCurrent ? 'text-accent' : 'text-text-main/40'
                        }`}>
                          {index + 1}
                        </span>
                      )}
                    </motion.div>
                    <motion.p
                      className={`text-xs font-medium text-center transition-colors duration-300 ${
                        isCurrent ? 'text-text-main' : 'text-text-main/50'
                      }`}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 + 0.1 }}
                    >
                      {phase.label}
                    </motion.p>
                  </div>
                  
                  {/* Connector Line */}
                  {index < phases.length - 1 && (
                    <div className="flex-1 h-[2px] -mt-8 relative">
                      <div className="absolute inset-0 bg-border-subtle" />
                      <motion.div
                        className="absolute inset-0 bg-accent"
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: index < currentPhaseIndex ? 1 : 0 }}
                        transition={{ duration: 0.5, ease: 'easeInOut' }}
                        style={{ transformOrigin: 'left' }}
                      />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Insights - Upper portion */}
      <div className="absolute top-40 left-0 right-0 px-12">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-wrap gap-3 justify-center">
            <AnimatePresence mode="popLayout">
              {insights.slice(0, 6).map((insight, index) => (
                <motion.div
                  key={insight.id}
                  initial={{ opacity: 0, scale: 0.8, y: -20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.8, y: -20 }}
                  transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
                  className="bg-surface-light rounded-lg shadow-sm px-4 py-2.5 border border-border-subtle/50 backdrop-blur-sm inline-flex items-center gap-2 max-w-md"
                >
                  <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-accent" />
                  <div className="text-sm text-text-main font-medium text-wrap prose prose-sm max-w-none prose-p:m-0">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{insight.text}</ReactMarkdown>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Main Status Text - Centered, 65% down */}
      <div className="flex-1 flex items-center justify-center">
        <div className="max-w-2xl mx-auto text-center relative" style={{ marginTop: '10vh' }}>
          {/* Breathing Ring Animation */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            {/* Multiple expanding rings */}
            {[0, 1, 2].map((index) => (
              <motion.div
                key={index}
                className="absolute rounded-full border-2 border-accent/40"
                style={{
                  width: '220px',
                  height: '220px',
                  filter: 'blur(1px)',
                }}
                animate={{
                  scale: [1, 2.2, 2.2],
                  opacity: [0.4, 0.15, 0],
                }}
                transition={{
                  duration: 4.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: index * 1.5,
                }}
              />
            ))}
            {/* Central pulsing circle */}
            <motion.div
              className="absolute rounded-full bg-accent/8"
              style={{
                width: '200px',
                height: '200px',
                filter: 'blur(4px)',
              }}
              animate={{
                scale: [1, 1.08, 1],
                opacity: [0.25, 0.4, 0.25],
              }}
              transition={{
                duration: 3.5,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          </div>
          
          {/* Text with shimmer effect */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentActivity}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="relative z-10"
            >
              <p className="text-3xl font-semibold tracking-tight text-text-main relative inline-block">
                {currentActivity}
                {/* Shimmer overlay */}
                <motion.span
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                  style={{
                    backgroundSize: '200% 100%',
                  }}
                  animate={{
                    backgroundPosition: ['-200% 0', '200% 0'],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                />
              </p>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Thin Progress Bar - Bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-border-subtle/30">
        <motion.div
          className="h-full bg-gradient-to-r from-accent to-accent/70"
          initial={{ width: '0%' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        />
      </div>
    </motion.div>
  );
};

export default ProcessingScreen;
