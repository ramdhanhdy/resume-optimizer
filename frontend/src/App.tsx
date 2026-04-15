
import React, { useState, useCallback, lazy, Suspense } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Screen } from './types';
import { useAuth } from './contexts/AuthContext';
import { LoginScreen, AuthCallback } from './components/auth';
import { LoadingSpinner } from './components/shared';
import InputScreen from './components/InputScreen';

// Lazy-load heavy screen components to reduce initial bundle
const ProcessingScreen = lazy(() => import('./components/ProcessingScreen'));
const RevealScreen = lazy(() => import('./components/RevealScreen'));

export interface AppState {
  applicationId?: number;
  resumeText?: string;
  jobText?: string;
  jobUrl?: string;
  linkedinUrl?: string;
  githubUsername?: string;
  githubToken?: string;
  forceRefreshProfile?: boolean;
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
  const { user, loading } = useAuth();
  const [screen, setScreen] = useState<Screen>(Screen.Input);
  const [appState, setAppState] = useState<AppState>({});

  // Debug auth state
  console.log('Auth state:', { user: user?.email, loading });

  const handleStartProcessing = useCallback((data: { 
    resumeText: string; 
    jobInput: string; 
    isUrl: boolean;
    linkedinUrl?: string;
    githubUsername?: string;
    githubToken?: string;
    jobTextFromPreview?: string;
    forceRefreshProfile?: boolean;
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
      forceRefreshProfile: data.forceRefreshProfile,
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

  // Handle OAuth callback route
  if (window.location.pathname === '/auth/callback') {
    return <AuthCallback />;
  }

  // Show loading while checking auth
  if (loading) {
    return <LoadingSpinner fullScreen message="Loading..." />;
  }

  // Show login if not authenticated
  if (!user) {
    return <LoginScreen />;
  }

  return (
    <div className="bg-background-main text-text-main min-h-screen">
      <AnimatePresence mode="wait">
        {screen === Screen.Input && (
          <InputScreen key="input" onStart={handleStartProcessing} />
        )}
        {screen === Screen.Processing && (
          <Suspense fallback={<LoadingSpinner fullScreen message="Preparing..." />}>
            <ProcessingScreen 
              key="processing" 
              onComplete={handleProcessingComplete}
              resumeText={appState.resumeText!}
              jobText={appState.jobText}
              jobUrl={appState.jobUrl}
              linkedinUrl={appState.linkedinUrl}
              githubUsername={appState.githubUsername}
              githubToken={appState.githubToken}
              forceRefreshProfile={appState.forceRefreshProfile}
            />
          </Suspense>
        )}
        {screen === Screen.Reveal && (
          <Suspense fallback={<LoadingSpinner fullScreen message="Loading results..." />}>
            <RevealScreen 
              key="reveal" 
              onRestart={handleRestart}
              applicationId={appState.applicationId!}
              scores={appState.validationScores}
            />
          </Suspense>
        )}
      </AnimatePresence>
    </div>
  );
};

export default App;
