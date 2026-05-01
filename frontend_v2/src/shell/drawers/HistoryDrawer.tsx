import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { Loader2, FileText, ChevronRight, AlertCircle } from 'lucide-react';
import { Drawer } from './Drawer';
import { listApplications, getApplicationReview } from '@/lib/api';
import type { ListApplicationsResponse } from '@/types/api';
import { useConversation } from '@/conversation/ConversationContext';
import { cn } from '@/lib/cn';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function HistoryDrawer({ isOpen, onClose }: HistoryDrawerProps) {
  const [loading, setLoading] = useState(false);
  const [loadingAppId, setLoadingAppId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [applications, setApplications] = useState<ListApplicationsResponse['applications']>([]);
  const { loadReview } = useConversation();

  useEffect(() => {
    if (!isOpen) return;
    
    let cancelled = false;
    setLoading(true);
    setError(null);
    
    listApplications()
      .then((res) => {
        if (cancelled) return;
        setApplications(res.applications);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load history');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
      
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  const handleSelect = async (appId: number) => {
    setLoadingAppId(appId);
    setError(null);
    
    try {
      const review = await getApplicationReview(appId);
      loadReview(review);
      onClose(); // Close drawer to reveal the loaded review
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load application');
    } finally {
      setLoadingAppId(null);
    }
  };

  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="History">
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-600">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-ink-400" />
        </div>
      ) : applications.length === 0 ? (
        <div className="flex h-40 flex-col items-center justify-center gap-3 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-ink-50">
            <FileText className="h-6 w-6 text-ink-300" />
          </div>
          <p className="text-sm font-medium text-ink-600">No applications yet</p>
          <p className="text-xs text-ink-400">Generations will appear here</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {applications.map((app) => (
            <li key={app.id}>
              <button
                onClick={() => handleSelect(app.id)}
                disabled={loadingAppId !== null}
                className={cn(
                  'group flex w-full flex-col gap-2 rounded-2xl bg-white/50 p-4 text-left transition-all',
                  'hover:bg-white focus:outline-none focus:ring-2 focus:ring-sky-300',
                  'ring-1 ring-ink-200/50 hover:shadow-sm hover:ring-ink-300/50',
                  loadingAppId === app.id ? 'opacity-70' : ''
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex flex-col">
                    <span className="font-semibold text-ink-900 line-clamp-1">
                      {app.job_title || 'Untitled Role'}
                    </span>
                    <span className="text-[13px] text-ink-500 line-clamp-1">
                      {app.company_name || 'Unknown Company'}
                    </span>
                  </div>
                  {loadingAppId === app.id ? (
                    <Loader2 className="h-4 w-4 animate-spin text-sky-500" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-ink-300 transition-transform group-hover:translate-x-0.5 group-hover:text-ink-500" />
                  )}
                </div>
                <div className="mt-1 flex items-center justify-between text-[11px] text-ink-400">
                  <span>{format(new Date(app.created_at), 'MMM d, yyyy')}</span>
                  <span className={cn(
                    'rounded-full px-2 py-0.5 font-medium',
                    app.status === 'completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-sky-50 text-sky-600'
                  )}>
                    {app.status}
                  </span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </Drawer>
  );
}
