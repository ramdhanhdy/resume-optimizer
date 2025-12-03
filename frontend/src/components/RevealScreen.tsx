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
import { FileText, Briefcase, Settings, CheckCircle, RotateCcw, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

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
      icon: <FileText className="w-4 h-4" />,
      available: !!reports?.optimized_resume_text,
    },
    {
      id: 'job' as TabType,
      label: 'Job Analysis',
      icon: <Briefcase className="w-4 h-4" />,
      available: !!reports?.job_analysis,
    },
    {
      id: 'optimization' as TabType,
      label: 'Optimization Report',
      icon: <Settings className="w-4 h-4" />,
      available: !!reports?.optimization_strategy,
    }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
         {/* Ambient Background */}
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-accent/5 rounded-full blur-[100px] pointer-events-none" />
         
        <div className="text-center relative z-10" role="status" aria-live="polite" aria-label="Loading reports">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full mx-auto mb-4"
            aria-hidden="true"
          />
          <p className="text-text-main font-medium">Finalizing results...</p>
        </div>
      </div>
    );
  }

  if (error || !reports) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface-light/50 backdrop-blur-xl border border-border shadow-2xl rounded-2xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-4">
             <RotateCcw className="w-8 h-8 text-destructive" />
          </div>
          <h2 className="text-xl font-bold text-text-main mb-2">Failed to Load Reports</h2>
          <p className="text-text-main/60 mb-6">{error}</p>
          <div className="space-y-2">
            <Button
              onClick={fetchReports}
              className="w-full bg-accent hover:bg-accent/90 text-white"
            >
              Try Again
            </Button>
            <Button
              onClick={onRestart}
              variant="outline"
              className="w-full"
            >
              Start New Application
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
       {/* Ambient Background */}
       <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-accent/5 rounded-full blur-[120px] pointer-events-none -z-10" />

      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-8 py-8">
          
          {/* Top HUD: Score & Actions */}
          <div className="grid md:grid-cols-[1fr_auto] gap-8 items-start mb-12">
             {/* Left: Score Hero */}
             <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 sm:gap-10">
                {/* Radial Score */}
                <div className="relative w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0">
                   <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="45" className="stroke-border-subtle fill-none" strokeWidth="8" />
                      <motion.circle
                         cx="50" cy="50" r="45"
                         className="stroke-accent fill-none"
                         strokeWidth="8"
                         strokeLinecap="round"
                         initial={{ pathLength: 0 }}
                         animate={{ pathLength: displayScores.overall_score / 100 }}
                         transition={{ duration: 1.5, ease: "easeOut" }}
                         strokeDasharray="1 1"
                      />
                   </svg>
                   <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-3xl sm:text-4xl font-bold text-text-main tracking-tighter">
                         {Math.round(displayScores.overall_score)}
                      </span>
                      <span className="text-[10px] uppercase tracking-widest text-text-main/50 font-semibold">Score</span>
                   </div>
                </div>

                {/* Metrics Grid */}
                <div className="flex-1 w-full sm:w-auto">
                   <h1 className="text-3xl font-bold text-text-main tracking-tight mb-2 text-center sm:text-left">
                      Analysis Complete
                   </h1>
                   <p className="text-text-main/60 mb-6 text-center sm:text-left">
                      Your resume has been optimized and tailored for the target role.
                   </p>
                   
                   <div className="grid grid-cols-3 gap-3 sm:gap-6">
                      <MetricCard label="Match" score={displayScores.requirements_match} />
                      <MetricCard label="ATS" score={displayScores.ats_optimization} />
                      <MetricCard label="Culture" score={displayScores.cultural_fit} />
                   </div>
                </div>
             </div>

             {/* Right: Actions */}
             <div className="flex flex-col gap-3 w-full sm:w-auto">
                <Button 
                   onClick={() => setExportModalOpen(true)}
                   className="w-full sm:w-48 bg-accent text-white hover:bg-accent/90 shadow-lg shadow-accent/20"
                >
                   Export Result
                </Button>
                <Button 
                   onClick={onRestart}
                   variant="ghost"
                   className="w-full sm:w-48 text-text-main/60 hover:text-text-main"
                >
                   Start New <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
             </div>
          </div>

          {/* Main Content Tabs */}
          <Tabs defaultValue="preview" value={activeTab} onValueChange={(value) => setActiveTab(value as TabType)} className="space-y-6">
            <div className="flex justify-center md:justify-start">
               <TabsList className="
                  bg-surface-light/50 backdrop-blur-md border border-white/20 p-1 
                  rounded-full shadow-sm inline-flex
               ">
                 {tabs.map((tab) => (
                   <TabsTrigger
                     key={tab.id}
                     value={tab.id}
                     disabled={!tab.available}
                     className="
                        rounded-full px-6 py-2.5 text-sm font-medium transition-all
                        data-[state=active]:bg-white data-[state=active]:text-accent data-[state=active]:shadow-sm
                        data-[state=inactive]:text-text-main/60 hover:text-text-main
                        flex items-center gap-2
                     "
                   >
                     {tab.icon}
                     {tab.label}
                   </TabsTrigger>
                 ))}
               </TabsList>
            </div>

            <div className="
               bg-surface-light/40 backdrop-blur-xl
               border border-white/20 shadow-2xl shadow-black/5
               rounded-3xl p-1 min-h-[600px]
            ">
               <div className="bg-white/50 rounded-[20px] w-full h-full p-6 sm:p-8 overflow-hidden">
                  <TabsContent value="preview" className="mt-0 focus-visible:outline-none h-full">
                    {reports.optimized_resume_text && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="h-full"
                      >
                        <ResumePreviewTab
                          resumeText={reports.optimized_resume_text}
                          applicationId={applicationId}
                        />
                      </motion.div>
                    )}
                  </TabsContent>

                  <TabsContent value="job" className="mt-0 focus-visible:outline-none">
                    {reports.job_analysis && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <JobAnalysisTab jobAnalysis={reports.job_analysis} />
                      </motion.div>
                    )}
                  </TabsContent>

                  <TabsContent value="optimization" className="mt-0 focus-visible:outline-none">
                    {reports.optimization_strategy && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <OptimizationReportTab optimizationStrategy={reports.optimization_strategy} />
                      </motion.div>
                    )}
                  </TabsContent>
               </div>
            </div>
          </Tabs>

      </div>

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

// Helper Component for Metrics
const MetricCard = ({ label, score }: { label: string; score: number }) => {
   // Color coding based on score
   const getColor = (s: number) => {
      if (s >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-100';
      if (s >= 60) return 'text-amber-600 bg-amber-50 border-amber-100';
      return 'text-rose-600 bg-rose-50 border-rose-100';
   };

   const colorClass = getColor(score);

   return (
      <div className={cn("flex flex-col items-center justify-center p-3 rounded-xl border", colorClass)}>
         <span className="text-2xl font-bold tracking-tight">{Math.round(score)}%</span>
         <span className="text-[10px] uppercase tracking-wider font-semibold opacity-80">{label}</span>
      </div>
   );
};

export default RevealScreen;
