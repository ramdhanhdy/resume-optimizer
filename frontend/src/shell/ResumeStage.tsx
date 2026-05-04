import { AnimatePresence, motion } from 'framer-motion';
import type { ReviewResume } from '@/types/review';
import { cn } from '@/lib/cn';

interface ResumeStageProps {
  resume: ReviewResume;
  /**
   * When true, dims the paper and overlays a soft sky shimmer so the
   * stage reads as "being rewritten" while a refinement is in flight.
   */
  refining?: boolean;
}

/**
 * Phase 5 right-hand stage: the optimized resume presented as a pristine
 * sheet of paper. Fades + lifts in softly so the handoff from processing
 * feels like the document materializing rather than a panel swapping.
 *
 * We deliberately show a plain-text rendering rather than a diff — the
 * spec wants a clean, confidence-building preview, not a technical view.
 */
export function ResumeStage({ resume, refining }: ResumeStageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, filter: 'blur(6px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, delay: 0.2, ease: [0.2, 0.7, 0.2, 1] }}
      className="relative flex-1 min-h-0 overflow-y-auto px-4 pb-16 sm:px-8"
      aria-label="Optimized resume preview"
      aria-busy={refining ? 'true' : undefined}
    >
      <div className="mx-auto w-full max-w-[720px] flex flex-col py-6 sm:py-8">
      {/* Filename ribbon — small label floating above the paper */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.4 }}
        className="mb-3 flex items-center gap-2 pl-2 text-[12px] text-ink-500"
      >
        <span className="block h-1.5 w-1.5 rounded-full bg-sky-400" />
        <span className="font-medium tracking-wide">{resume.filename}</span>
      </motion.div>

      {/* The paper */}
      <motion.article
        layout
        animate={{
          opacity: refining ? 0.45 : 1,
          filter: refining ? 'blur(1.5px)' : 'blur(0px)',
        }}
        transition={{ duration: 0.4, ease: [0.2, 0.7, 0.2, 1] }}
        className={cn(
          'relative rounded-xl bg-white',
          'ring-1 ring-ink-100',
          refining && 'ring-sky-200',
        )}
        style={{
          // Layered soft shadows: bottom for depth, top for the "lit from
          // above" feeling that makes it read as paper and not a card.
          boxShadow:
            '0 1px 2px rgba(15, 23, 42, 0.04), 0 18px 40px -12px rgba(56, 120, 200, 0.18), 0 40px 80px -20px rgba(15, 23, 42, 0.12)',
        }}
      >
        {/* Subtle top highlight */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-24"
          style={{
            background:
              'linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 100%)',
          }}
        />

        <div className="relative px-10 py-12">
          <pre
            className={cn(
              'whitespace-pre-wrap break-words font-serif text-[13.5px] leading-[1.65] text-ink-800',
              'sm:text-[14px]',
            )}
            // font-serif via Tailwind uses the default serif stack — this
            // is intentional; makes the preview feel like a Word/PDF doc
            // rather than a chat-panel code block.
          >
            {resume.plain_text}
          </pre>
        </div>
      </motion.article>

      {/* Shimmer overlay — fades in over the paper while a refinement
          is in-flight. The underlying text stays dimly legible so the
          continuity with the finished resume is preserved. */}
      <AnimatePresence>
        {refining && (
          <motion.div
            key="refining-shimmer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 flex items-start justify-center"
          >
            <div className="sticky top-20 h-[60vh] w-full max-w-[720px] overflow-hidden rounded-xl">
              {/* Soft radial wash */}
              <motion.div
                animate={{ opacity: [0.35, 0.6, 0.35] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute inset-0"
                style={{
                  background:
                    'radial-gradient(ellipse at center, rgba(125, 170, 255, 0.28) 0%, rgba(200, 220, 255, 0.1) 45%, transparent 75%)',
                  filter: 'blur(20px)',
                }}
              />
              {/* Sweeping highlight band */}
              <motion.div
                animate={{ x: ['-100%', '100%'] }}
                transition={{
                  duration: 2.2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                className="absolute inset-y-0 w-[40%]"
                style={{
                  background:
                    'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.55) 50%, transparent 100%)',
                  filter: 'blur(10px)',
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>
    </motion.div>
  );
}
