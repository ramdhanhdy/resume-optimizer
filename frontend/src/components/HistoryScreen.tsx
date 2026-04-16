/**
 * HistoryScreen Component
 *
 * Read-only list of past resume optimization applications.
 * Uses GET /api/applications to fetch data.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Clock, ArrowLeft, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiClient } from '../services/api';
import { useReducedMotion } from '@/design-system/animations';
import { slideUpVariants } from '@/design-system/animations/variants';

interface ApplicationRecord {
  id: number;
  company_name: string;
  job_title: string;
  created_at: string;
  status: string;
}

interface HistoryScreenProps {
  onBack: () => void;
  onViewApplication?: (applicationId: number) => void;
}

export default function HistoryScreen({ onBack, onViewApplication }: HistoryScreenProps) {
  const prefersReducedMotion = useReducedMotion();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const res = await apiClient.listApplications();
        setApplications(res.applications || []);
      } catch (e) {
        console.error('Failed to fetch applications:', e);
        setError('Failed to load history.');
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, []);

  return (
    <motion.div
      variants={prefersReducedMotion ? undefined : slideUpVariants}
      initial={prefersReducedMotion ? undefined : "initial"}
      animate={prefersReducedMotion ? undefined : "animate"}
      className="min-h-screen flex flex-col items-center p-4 sm:p-6 lg:p-8 bg-gradient-to-br from-[#FAF9F6] via-[#F5F3EE] to-[#EEF2F1]"
    >
      <div className="w-full max-w-3xl">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="ghost" size="sm" onClick={onBack} className="text-text-main/60 hover:text-text-main">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back
          </Button>
          <h1 className="text-2xl font-bold text-text-main">Optimization History</h1>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-accent/20 border-t-accent rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center py-20 text-destructive">{error}</div>
        )}

        {/* Empty state */}
        {!loading && !error && applications.length === 0 && (
          <div className="text-center py-20">
            <FileText className="w-12 h-12 text-text-main/20 mx-auto mb-4" />
            <p className="text-text-main/50 text-lg">No optimization history yet.</p>
            <p className="text-text-main/30 text-sm mt-1">Your completed runs will appear here.</p>
          </div>
        )}

        {/* Application list */}
        {!loading && !error && applications.length > 0 && (
          <div className="space-y-3">
            {applications.map((app) => (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-xl p-4 sm:p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-text-main truncate">
                      {app.job_title || 'Untitled Position'}
                    </h3>
                    <p className="text-sm text-text-main/50 mt-0.5 truncate">
                      {app.company_name || 'Unknown Company'}
                    </p>
                    <div className="flex items-center gap-1.5 mt-2 text-xs text-text-main/30">
                      <Clock className="w-3 h-3" />
                      {new Date(app.created_at).toLocaleDateString(undefined, {
                        year: 'numeric', month: 'short', day: 'numeric',
                      })}
                    </div>
                  </div>
                  {onViewApplication && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewApplication(app.id)}
                      className="text-accent hover:text-accent/80 shrink-0"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
