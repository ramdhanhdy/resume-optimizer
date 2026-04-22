import { AnimatePresence, motion } from 'framer-motion';
import { Download, Loader2, Sparkles } from 'lucide-react';
import { useCallback, useState } from 'react';
import type { ApplicationReview } from '@/types/review';
import { fetchAuthenticatedBlob } from '@/lib/api';
import { cn } from '@/lib/cn';

interface ReviewActionsProps {
  review?: ApplicationReview;
}

/**
 * Phase 5 contextual action bar. Renders in place of the text input when
 * the active agent message has `ui.kind === 'review'`.
 *
 *   [ ⬇ Download .docx ]    ← primary, sky-glow
 *   [ Make it shorter ]     ← tweak secondary
 *   [ Sound more professional ] ← tweak secondary
 *
 * Clicking a tweak pill fades the whole bar out, pretends to process for
 * ~3s with a small inline spinner, then fades back in. The actual
 * document-edit flow is left for a future iteration; for now the visual
 * loop is enough to communicate "the system is working on your tweak".
 */
export function ReviewActions({ review }: ReviewActionsProps) {
  const [tweaking, setTweaking] = useState<string | null>(null);

  const downloadPlainText = useCallback((reviewPayload: ApplicationReview) => {
    const blob = new Blob([reviewPayload.resume.plain_text], {
      type: 'text/plain;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = reviewPayload.resume.filename.replace(/\.(docx|pdf)$/i, '.txt');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  const handleDownload = useCallback(() => {
    if (!review) return;
    if (review.exports.docx_url) {
      void (async () => {
        try {
          const { blob, filename } = await fetchAuthenticatedBlob(review.exports.docx_url!);
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename ?? review.resume.filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } catch {
          downloadPlainText(review);
        }
      })();
      return;
    }
    downloadPlainText(review);
  }, [downloadPlainText, review]);

  const handleTweak = useCallback((label: string) => {
    setTweaking(label);
    window.setTimeout(() => setTweaking(null), 3000);
  }, []);

  return (
    <div className="flex min-h-[3.5rem] w-full flex-col items-start gap-2">
      <AnimatePresence mode="wait">
        {tweaking ? (
          <motion.div
            key="tweaking"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -2 }}
            transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
            className={cn(
              'inline-flex items-center gap-2 rounded-full glass-sky px-4 py-2',
              'text-[13px] text-ink-600 ring-1 ring-sky-200/60 soft-shadow',
            )}
          >
            <Loader2 className="h-3.5 w-3.5 animate-spin text-sky-500" strokeWidth={2} />
            <span>Rewriting · {tweaking.toLowerCase()}…</span>
          </motion.div>
        ) : (
          <motion.div
            key="actions"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -2 }}
            transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
            className="flex flex-wrap items-center gap-2"
          >
            <PrimaryPill onClick={handleDownload} disabled={!review}>
              <Download className="h-4 w-4" strokeWidth={2} />
              <span>Download {review?.resume.filename?.split('.').pop() ?? 'docx'}</span>
            </PrimaryPill>
            <TweakPill onClick={() => handleTweak('Make it shorter')}>
              Make it shorter
            </TweakPill>
            <TweakPill onClick={() => handleTweak('Sound more professional')}>
              Sound more professional
            </TweakPill>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function PrimaryPill({
  children,
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.97 }}
      className={cn(
        'relative inline-flex items-center gap-2 rounded-full px-4 py-2',
        'text-[14px] font-medium text-white',
        'bg-gradient-to-r from-sky-500 to-sky-400',
        'ring-1 ring-sky-400/60 transition',
        'disabled:cursor-not-allowed disabled:opacity-50',
      )}
      style={{
        // Soft blue halo so it reads as the primary CTA without shouting.
        boxShadow:
          '0 0 0 1px rgba(56, 189, 248, 0.25), 0 10px 30px -10px rgba(56, 189, 248, 0.55), 0 0 24px rgba(125, 170, 255, 0.4)',
      }}
    >
      <Sparkles
        className="absolute -left-1 -top-1 h-3 w-3 text-sky-200"
        strokeWidth={2.25}
        aria-hidden="true"
      />
      {children}
    </motion.button>
  );
}

function TweakPill({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.97 }}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-3.5 py-2',
        'text-[13px] text-ink-700 glass-sky soft-shadow',
        'ring-1 ring-sky-200/60 transition hover:text-ink-900 hover:ring-sky-300',
      )}
    >
      {children}
    </motion.button>
  );
}
