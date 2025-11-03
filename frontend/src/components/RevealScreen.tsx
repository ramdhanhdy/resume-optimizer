import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import React from 'react';
import {
  JobAnalysisTab,
  OptimizationReportTab,
  ResumePreviewTab
} from './tabs';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import ExportModal from './ExportModal';

interface RevealScreenProps {
  onRestart: () => void;
  applicationId: number;
  scores?: {
    overall: number;
    requirements_match: number;
    ats_optimization: number;
    cultural_fit: number;
  };
}

interface Reports {
  job_analysis: any;
  optimization_strategy: any;
  validation_report: any;
  optimized_resume_text: string;
  validation_scores: {
    overall_score: number;
    requirements_match: number;
    ats_optimization: number;
    cultural_fit: number;
  };
}

type TabType = 'preview' | 'job' | 'optimization';

const RevealScreen: React.FC<RevealScreenProps> = ({ onRestart, applicationId, scores }) => {
  const [activeTab, setActiveTab] = useState<TabType>('preview');
  const [reports, setReports] = useState<Reports | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);

  useEffect(() => {
    fetchReports();
  }, [applicationId]);

  const fetchReports = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/application/${applicationId}/reports`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch reports: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        setReports(data.reports);
      } else {
        throw new Error('Failed to load reports');
      }
    } catch (err) {
      console.error('Error fetching reports:', err);
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setIsLoading(false);
    }
  };

  // Use scores from reports if available, fallback to props
  const displayScores = reports?.validation_scores || {
    overall_score: scores?.overall || 0,
    requirements_match: scores?.requirements_match || 0,
    ats_optimization: scores?.ats_optimization || 0,
    cultural_fit: scores?.cultural_fit || 0
  };

  const tabs = [
    {
      id: 'preview' as TabType,
      label: 'Resume Preview',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      available: !!reports?.optimized_resume_text,
      badge: displayScores.overall_score
    },
    {
      id: 'job' as TabType,
      label: 'Job Analysis',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      available: !!reports?.job_analysis,
      badge: displayScores.requirements_match
    },
    {
      id: 'optimization' as TabType,
      label: 'Optimization Report',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      available: !!reports?.optimization_strategy,
      badge: displayScores.ats_optimization
    }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background-main flex items-center justify-center">
        <div className="text-center" role="status" aria-live="polite" aria-label="Loading reports">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full mx-auto mb-4"
            aria-hidden="true"
          />
          <p className="text-text-main">Loading reports...</p>
        </div>
      </div>
    );
  }

  if (error || !reports) {
    return (
      <div className="min-h-screen bg-background-main flex items-center justify-center p-4">
        <div className="bg-surface-light rounded-lg shadow-lg p-8 max-w-md w-full text-center" role="alert" aria-live="assertive">
          <svg className="w-16 h-16 text-destructive mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-bold text-text-main mb-2">Failed to Load Reports</h2>
          <p className="text-text-muted mb-6">{error}</p>
          <div className="space-y-2">
            <Button
              onClick={fetchReports}
              className="w-full"
              aria-label="Try loading reports again"
            >
              Try Again
            </Button>
            <Button
              onClick={onRestart}
              variant="outline"
              className="w-full"
              aria-label="Start a new resume optimization"
            >
              Start New Application
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background-main">
      <Tabs defaultValue="preview" value={activeTab} onValueChange={(value) => setActiveTab(value as TabType)}>
        {/* Tab navigation - at top like ProcessingScreen phases */}
        <div className="pt-8 sm:pt-12 px-4 sm:px-12">
          <div className="max-w-6xl mx-auto">
            {/* Header with restart button */}
            <div className="flex items-center justify-between mb-6 sm:mb-8">
              <h1 className="text-2xl sm:text-3xl font-semibold text-text-main tracking-tight">
                Analysis Complete
              </h1>
              <Button
                onClick={onRestart}
                variant="link"
                className="text-sm font-medium text-primary hover:text-primary/80"
                aria-label="Start a new resume optimization"
              >
                Start New →
              </Button>
            </div>

            {/* Tabs */}
            <TabsList className="w-full sm:w-auto grid grid-cols-3 sm:inline-flex h-auto sm:h-9 bg-transparent gap-1 sm:gap-2 p-0">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  disabled={!tab.available}
                  className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2.5 sm:py-3 rounded-lg font-medium text-xs sm:text-sm whitespace-nowrap transition-all duration-200 border data-[state=active]:bg-surface-light data-[state=active]:border-border-subtle data-[state=active]:shadow-subtle data-[state=active]:text-text-main data-[state=inactive]:bg-transparent data-[state=inactive]:border-transparent data-[state=inactive]:text-text-main/60 hover:text-text-main hover:bg-surface-light/50 disabled:opacity-40 disabled:cursor-not-allowed"
                  aria-label={`${tab.label} tab`}
                >
                  <span className="w-4 h-4 sm:w-5 sm:h-5" aria-hidden="true">
                    {tab.icon}
                  </span>
                  <span className="hidden sm:inline">{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span className={`
                      px-1.5 sm:px-2 py-0.5 rounded text-xs font-semibold
                      ${tab.badge >= 80 ? 'bg-accent text-white' :
                        tab.badge >= 60 ? 'bg-primary text-white' :
                        'bg-warning text-white'}
                    `}>
                      {tab.badge}%
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>
        </div>

        {/* Tab content */}
        <div className="flex-1 px-4 sm:px-12 py-6 sm:py-8">
          <div className="max-w-6xl mx-auto">
            <TabsContent value="preview" aria-label="Resume preview content" className="mt-0">
              {reports.optimized_resume_text && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
                >
                  <ResumePreviewTab
                    resumeText={reports.optimized_resume_text}
                    applicationId={applicationId}
                  />
                </motion.div>
              )}
            </TabsContent>

            <TabsContent value="job" aria-label="Job analysis content" className="mt-0">
              {reports.job_analysis && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
                >
                  <JobAnalysisTab jobAnalysis={reports.job_analysis} />
                </motion.div>
              )}
            </TabsContent>

            <TabsContent value="optimization" aria-label="Optimization report content" className="mt-0">
              {reports.optimization_strategy && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
                >
                  <OptimizationReportTab optimizationStrategy={reports.optimization_strategy} />
                </motion.div>
              )}
            </TabsContent>
          </div>
        </div>
      </Tabs>

      {/* Export Modal */}
      <ExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        onRestart={onRestart}
        applicationId={applicationId}
      />
    </div>
  );
};

export default RevealScreen;
