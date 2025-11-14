
import React, { useState, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Screen } from './types';
import InputScreen from './components/InputScreen';
import ProcessingScreen from './components/ProcessingScreen';
import RevealScreen from './components/RevealScreen';

export interface AppState {
  applicationId?: number;
  resumeText?: string;
  jobText?: string;
  jobUrl?: string;
  linkedinUrl?: string;
  githubUsername?: string;
  githubToken?: string;
  companyName?: string;
  jobTitle?: string;
  validationScores?: {
    overall: number;
    requirements_match: number;
    ats_optimization: number;
    cultural_fit: number;
  };
}

const App: React.FC = () => {
  const [screen, setScreen] = useState<Screen>(Screen.Input);
  const [appState, setAppState] = useState<AppState>({});

  const handleStartProcessing = useCallback((data: { 
    resumeText: string; 
    jobInput: string; 
    isUrl: boolean;
    linkedinUrl?: string;
    githubUsername?: string;
    githubToken?: string;
    jobTextFromPreview?: string;
  }) => {
    setAppState(prev => ({
      ...prev,
      resumeText: data.resumeText,
      // If the job input is a URL and we have a preview text, prefer the
      // fetched/sanitized text while still keeping the original URL.
      jobText: data.isUrl ? data.jobTextFromPreview : data.jobInput,
      jobUrl: data.isUrl ? data.jobInput : undefined,
      linkedinUrl: data.linkedinUrl,
      githubUsername: data.githubUsername,
      githubToken: data.githubToken,
    }));
    setScreen(Screen.Processing);
  }, []);

  const handleProcessingComplete = useCallback((completedAppState: Partial<AppState>) => {
    setAppState(prev => ({ ...prev, ...completedAppState }));
    setScreen(Screen.Reveal);
  }, []);
  
  const handleRestart = useCallback(() => {
    setAppState({});
    setScreen(Screen.Input);
  }, []);

  return (
    <div className="bg-background-main text-text-main min-h-screen">
      <AnimatePresence mode="wait">
        {screen === Screen.Input && (
          <InputScreen key="input" onStart={handleStartProcessing} />
        )}
        {screen === Screen.Processing && (
          <ProcessingScreen 
            key="processing" 
            onComplete={handleProcessingComplete}
            resumeText={appState.resumeText!}
            jobText={appState.jobText}
            jobUrl={appState.jobUrl}
            linkedinUrl={appState.linkedinUrl}
            githubUsername={appState.githubUsername}
            githubToken={appState.githubToken}
          />
        )}
        {screen === Screen.Reveal && (
          <RevealScreen 
            key="reveal" 
            onRestart={handleRestart}
            applicationId={appState.applicationId!}
            scores={appState.validationScores}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default App;
