
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PROCESSING_ACTIVITIES, PROCESSING_PHASES, MOCK_INSIGHTS } from '../constants';
import type { Insight } from '../types';
import { useProcessingJob } from '../hooks/useProcessingJob';
import { apiClient } from '../services/api';

interface ProcessingScreenProps {
  onComplete: (appState: any) => void;
  resumeText: string;
  jobText?: string;
  jobUrl?: string;
}

const TOTAL_DURATION = 12000; // 12 seconds estimate

// Feature flag for streaming (set to true to use new streaming infrastructure)
const USE_STREAMING = true;

const ProcessingScreen: React.FC<ProcessingScreenProps> = ({ onComplete, resumeText, jobText, jobUrl }) => {
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
      className="min-h-screen flex flex-col p-12"
    >
        <div className="fixed top-8 left-12">
            <AnimatePresence mode="wait">
                <motion.p
                    key={currentPhase}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-sm font-medium text-text-main/70"
                >
                    {currentPhase}
                </motion.p>
            </AnimatePresence>
        </div>

      <div className="flex-grow flex items-center">
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid grid-cols-10 gap-12">
            <div className="col-span-6 flex items-center">
              <motion.div 
                className="bg-surface-light rounded-lg shadow-subtle p-8 border border-border-subtle/50 w-full animate-pulse-slow"
              >
                <AnimatePresence mode="wait">
                  <motion.p
                    key={currentActivity}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-2xl font-medium tracking-tight"
                  >
                    {currentActivity}
                  </motion.p>
                </AnimatePresence>
              </motion.div>
            </div>

            <div className="col-span-4 space-y-3 h-[360px] flex flex-col-reverse overflow-hidden">
              <AnimatePresence mode="popLayout">
                {insights.slice(0, 5).map((insight, index) => (
                  <motion.div
                    key={insight.id}
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ 
                      opacity: 1 - (index * 0.15), 
                      y: 0,
                      scale: 1 - (index * 0.02)
                    }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
                    className="bg-surface-light rounded-lg shadow-subtle p-4 border border-border-subtle/50 backdrop-blur-sm"
                    style={{
                      marginTop: index === 0 ? 0 : -8,
                      zIndex: 5 - index,
                    }}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-2 h-2 rounded-full bg-accent mt-1.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-main leading-relaxed">
                          {insight.text}
                        </p>
                        <p className="text-xs text-text-main/60 mt-1.5 uppercase tracking-wide font-medium">
                          {insight.category}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
      
      <div className="fixed bottom-0 left-0 right-0 h-[3px] bg-border-subtle/50">
        <motion.div
          className="h-full bg-accent"
          initial={{ width: '0%' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.1, ease: "linear" }}
        />
      </div>
    </motion.div>
  );
};

export default ProcessingScreen;
