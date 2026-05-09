import { useState } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, FileText } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ReviewMobileTabsProps {
  summaryPanel: React.ReactNode;
  previewPanel: React.ReactNode;
}

/**
 * Mobile-only tab switcher for the REVIEWING phase.
 *
 * On viewports below the `lg` breakpoint the two-column desktop layout
 * collapses to a single column. Rather than forcing an extremely long
 * vertical scroll, we expose two tabs — Summary (chat + composer) and
 * Preview (resume paper) — so the user can jump between them.
 */
export function ReviewMobileTabs({ summaryPanel, previewPanel }: ReviewMobileTabsProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'preview'>('summary');

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Tab bar */}
      <div className="shrink-0 flex items-center gap-1 rounded-full bg-white/60 p-1 ring-1 ring-ink-100/60 backdrop-blur-sm">
        <TabButton
          active={activeTab === 'summary'}
          onClick={() => setActiveTab('summary')}
          icon={<MessageSquare className="h-3.5 w-3.5" strokeWidth={2} />}
          label="Summary"
        />
        <TabButton
          active={activeTab === 'preview'}
          onClick={() => setActiveTab('preview')}
          icon={<FileText className="h-3.5 w-3.5" strokeWidth={2} />}
          label="Preview"
        />
      </div>

      {/* Panel content */}
      <div className="flex-1 min-h-0 overflow-hidden pt-2">
        {activeTab === 'summary' ? (
          <div className="flex h-full flex-col">{summaryPanel}</div>
        ) : (
          <div className="h-full">{previewPanel}</div>
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative flex flex-1 items-center justify-center gap-1.5 rounded-full py-1.5 text-[13px] font-medium transition',
        active ? 'text-ink-800' : 'text-ink-400 hover:text-ink-600',
      )}
    >
      {active && (
        <motion.div
          layoutId="review-tab-indicator"
          className="absolute inset-0 rounded-full bg-white shadow-sm ring-1 ring-ink-100/80"
          transition={{ type: 'spring', duration: 0.4, bounce: 0.15 }}
        />
      )}
      <span className="relative z-10 flex items-center gap-1.5">
        {icon}
        {label}
      </span>
    </button>
  );
}
