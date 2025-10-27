
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PROCESSING_ACTIVITIES, PROCESSING_PHASES, MOCK_INSIGHTS } from '../constants';
import type { Insight } from '../types';

interface ProcessingScreenProps {
  onComplete: (appState: any) => void;
  resumeText: string;
  jobText?: string;
  jobUrl?: string;
}

const TOTAL_DURATION = 12000; // 12 seconds estimate

const ProcessingScreen: React.FC<ProcessingScreenProps> = ({ onComplete, resumeText, jobText, jobUrl }) => {
  const [currentActivity, setCurrentActivity] = useState(PROCESSING_ACTIVITIES[0]);
  const [currentPhase, setCurrentPhase] = useState(PROCESSING_PHASES[0]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [progress, setProgress] = useState(0);
  const hasStartedRef = React.useRef(false);

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

            <div className="col-span-4 space-y-3 h-[280px] flex flex-col justify-end">
              <AnimatePresence>
                {insights.map((insight) => (
                  <motion.div
                    key={insight.id}
                    layout
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="bg-surface-light rounded-lg shadow-subtle p-4 border border-border-subtle/50"
                  >
                    <p className="text-sm font-medium text-text-main">"{insight.text}"</p>
                    <p className="text-xs text-text-main/70 mt-1">{insight.category}</p>
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
