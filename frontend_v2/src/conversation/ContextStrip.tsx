import type { ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Briefcase, FileText, Sparkles, Target } from 'lucide-react';
import type { CollectedData } from './types';
import { cn } from '@/lib/cn';

interface Chip {
  key: string;
  icon: ReactNode;
  label: string;
  /** Tooltip / full value. */
  full?: string;
}

/**
 * Translates the reducer's `CollectedData` into a stable list of chips.
 * Only data the user has actually provided surfaces here — so the strip
 * grows turn-by-turn as the conversation progresses.
 */
function chipsFromData(data: CollectedData): Chip[] {
  const chips: Chip[] = [];

  if (data.resumeFile) {
    chips.push({
      key: 'resume',
      icon: <FileText className="h-3.5 w-3.5" strokeWidth={1.75} />,
      label: data.resumeFile.name,
      full: `${data.resumeFile.name} · ${Math.round(data.resumeFile.size / 1024)} kb`,
    });
  } else if (data.resumeText) {
    const preview = data.resumeText.slice(0, 60);
    chips.push({
      key: 'resume',
      icon: <FileText className="h-3.5 w-3.5" strokeWidth={1.75} />,
      label: 'Pasted resume',
      full: preview + (data.resumeText.length > 60 ? '…' : ''),
    });
  }

  if (data.jobInput) {
    let label = data.jobInput;
    if (data.jobIsUrl) {
      try {
        label = new URL(data.jobInput).hostname.replace(/^www\./, '');
      } catch {
        label = data.jobInput.length > 30 ? data.jobInput.slice(0, 28) + '…' : data.jobInput;
      }
    } else if (label.length > 30) {
      label = label.slice(0, 28) + '…';
    }
    chips.push({
      key: 'job',
      icon: <Target className="h-3.5 w-3.5" strokeWidth={1.75} />,
      label,
      full: data.jobInput,
    });
  }

  if (data.experienceLevel) {
    const labels: Record<string, string> = {
      junior: 'Junior',
      mid: 'Mid-level',
      senior: 'Senior',
      lead: 'Lead / Staff',
    };
    chips.push({
      key: 'level',
      icon: <Briefcase className="h-3.5 w-3.5" strokeWidth={1.75} />,
      label: labels[data.experienceLevel] ?? data.experienceLevel,
    });
  }

  if (data.tonePreference) {
    const labels: Record<string, string> = {
      concise: 'Concise',
      balanced: 'Balanced',
      detailed: 'Detailed',
    };
    chips.push({
      key: 'tone',
      icon: <Sparkles className="h-3.5 w-3.5" strokeWidth={1.75} />,
      label: labels[data.tonePreference] ?? data.tonePreference,
    });
  }

  return chips;
}

/**
 * Persistent "dossier" of what the user has shared so far. Sits just
 * below the header so the center stage can stay clean — one hero line
 * at a time — while the accumulated context remains glance-able.
 */
export function ContextStrip({ data }: { data: CollectedData }) {
  const chips = chipsFromData(data);
  if (chips.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex w-full max-w-xl flex-wrap items-center justify-center gap-1.5"
    >
      <AnimatePresence mode="popLayout" initial={false}>
        {chips.map((c) => (
          <motion.span
            key={c.key}
            layout
            initial={{ opacity: 0, scale: 0.85, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85 }}
            transition={{ duration: 0.3, ease: [0.2, 0.7, 0.2, 1] }}
            title={c.full ?? c.label}
            className={cn(
              'glass inline-flex max-w-[22ch] items-center gap-1.5 truncate rounded-full',
              'px-2.5 py-1 text-[12px] text-ink-600',
              'ring-1 ring-sky-200/60',
            )}
          >
            <span className="shrink-0 text-ink-400">{c.icon}</span>
            <span className="truncate">{c.label}</span>
          </motion.span>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
