
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

  const handleStartProcessing = useCallback((data: { resumeText: string; jobInput: string; isUrl: boolean }) => {
    setAppState(prev => ({
      ...prev,
      resumeText: data.resumeText,
      jobText: data.isUrl ? undefined : data.jobInput,
      jobUrl: data.isUrl ? data.jobInput : undefined,
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
