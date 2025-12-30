import { Zap, Crown } from 'lucide-react';
import { useUsage } from '../../hooks/useUsage';

export default function UsageMeter() {
  const { remaining, total, isSubscribed, loading } = useUsage();

  if (loading) return null;

  if (isSubscribed) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-full text-xs font-medium text-amber-700">
        <Crown className="w-3.5 h-3.5" />
        <span>Pro Plan</span>
      </div>
    );
  }

  const percentage = (remaining / total) * 100;

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1.5 text-xs text-text-main/60">
        <Zap className="w-3.5 h-3.5 text-accent" />
        <span>{remaining}/{total} free</span>
      </div>
      <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            percentage > 40 ? 'bg-accent' : percentage > 20 ? 'bg-amber-500' : 'bg-destructive'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
