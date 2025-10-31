import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import React from 'react';
import {
  ValidationDetailsTab,
  JobAnalysisTab,
  OptimizationReportTab,
  ResumePreviewTab
} from './tabs';

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

type TabType = 'preview' | 'validation' | 'job' | 'optimization';

const RevealScreen: React.FC<RevealScreenProps> = ({ onRestart, applicationId, scores }) => {
  const [activeTab, setActiveTab] = useState<TabType>('preview');
  const [reports, setReports] = useState<Reports | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      available: !!reports?.optimized_resume_text
    },
    {
      id: 'validation' as TabType,
      label: 'Validation Details',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      badge: displayScores.overall_score,
      available: !!reports?.validation_report
    },
    {
      id: 'job' as TabType,
      label: 'Job Analysis',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      available: !!reports?.job_analysis
    },
    {
      id: 'optimization' as TabType,
      label: 'Optimization Report',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      available: !!reports?.optimization_strategy
    }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-gray-600">Loading reports...</p>
        </div>
      </div>
    );
  }

  if (error || !reports) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Failed to Load Reports</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="space-y-2">
            <button
              onClick={fetchReports}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={onRestart}
              className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Start New Application
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background-main">
      {/* Tab navigation - at top like ProcessingScreen phases */}
      <div className="pt-12 px-12">
        <div className="max-w-6xl mx-auto">
          {/* Header with restart button */}
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-semibold text-text-main tracking-tight">
              Analysis Complete
            </h1>
            <button
              onClick={onRestart}
              className="text-sm font-medium text-primary hover:text-primary/80 transition-colors"
            >
              Start New Application →
            </button>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-2">
            {tabs.map((tab, index) => {
              const isActive = activeTab === tab.id;

              return (
                <React.Fragment key={tab.id}>
                  <button
                    onClick={() => tab.available && setActiveTab(tab.id)}
                    disabled={!tab.available}
                    className={`
                      flex items-center gap-2 px-5 py-3 rounded-lg font-medium text-sm whitespace-nowrap
                      transition-all duration-200 border
                      ${isActive
                        ? 'bg-surface-light border-border-subtle shadow-subtle text-text-main'
                        : 'bg-transparent border-transparent text-text-main/60 hover:text-text-main hover:bg-surface-light/50'
                      }
                      ${!tab.available ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    <span className="w-5 h-5">
                      {tab.icon}
                    </span>
                    <span>{tab.label}</span>
                    {tab.badge !== undefined && (
                      <span className={`
                        px-2 py-0.5 rounded text-xs font-semibold
                        ${tab.badge >= 80 ? 'bg-accent text-white' :
                          tab.badge >= 60 ? 'bg-primary text-white' :
                          'bg-warning text-white'}
                      `}>
                        {tab.badge}%
                      </span>
                    )}
                  </button>

                  {/* Divider between tabs */}
                  {index < tabs.length - 1 && (
                    <div className="h-6 w-px bg-border-subtle/50" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 px-12 py-8">
        <div className="max-w-6xl mx-auto">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
          >
            {activeTab === 'preview' && reports.optimized_resume_text && (
              <ResumePreviewTab
                resumeText={reports.optimized_resume_text}
                applicationId={applicationId}
              />
            )}

            {activeTab === 'validation' && reports.validation_report && (
              <ValidationDetailsTab validationReport={reports.validation_report} />
            )}

            {activeTab === 'job' && reports.job_analysis && (
              <JobAnalysisTab jobAnalysis={reports.job_analysis} />
            )}

            {activeTab === 'optimization' && reports.optimization_strategy && (
              <OptimizationReportTab optimizationStrategy={reports.optimization_strategy} />
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default RevealScreen;
