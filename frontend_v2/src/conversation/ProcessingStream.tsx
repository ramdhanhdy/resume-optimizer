import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { STEP_LABELS, type StepName } from '@/types/streaming';
import { useProcessingJob } from './useProcessingJob';
import { useConversation } from './ConversationContext';
import { useTypewriter } from './useTypewriter';
import { getApplicationReview, startPipeline, MOCK_STREAM } from '@/lib/api';
import { cn } from '@/lib/cn';

/**
 * Phase 4: live-stream processing stage.
 *
 * When the conversation phase flips to PROCESSING this component takes over
 * the center stage. It:
 *   1. Kicks off the pipeline (uploading the resume file first if needed).
 *   2. Subscribes to the SSE stream via `useProcessingJob`.
 *   3. Renders each step the stream enters as a stacked message — older
 *      steps fade up/out as newer ones appear, and the active step glows
 *      with a typewriter reveal.
 *   4. Transitions the conversation to REVIEWING once `isComplete`.
 *
 * In dev, set `VITE_MOCK_STREAM=true` to replay a scripted timeline
 * without needing the backend.
 */
export function ProcessingStream() {
  const { state, completeProcessing } = useConversation();
  const [jobId, setJobId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const startedRef = useRef(false);

  // Step-by-step log rendered on the stage. We append an entry the first
  // time we see each StepName in `currentStep`.
  const [stepLog, setStepLog] = useState<StepName[]>([]);

  // --- 1) Start the pipeline on mount ---
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    if (MOCK_STREAM) {
      // No real backend call; just invent a job id and let the hook's
      // scripted stream take over.
      setJobId(`mock-${Date.now().toString(36)}`);
      return;
    }

    (async () => {
      try {
        let resumeText = state.data.resumeText ?? '';
        let resumeFilename: string | undefined;

        if (state.data.resumeFile && !resumeText) {
          // We only have metadata in state — fetch the File from the
          // attachment flow. Since we don't persist File objects, fall
          // back to whatever text the user pasted. A future refinement is
          // to re-prompt or upload from the captured File.
          resumeFilename = state.data.resumeFile.name;
        }

        if (!resumeText) {
          throw new Error(
            'No resume text available. Re-attach or paste your resume and try again.',
          );
        }

        const response = await startPipeline({
          resume_text: resumeText,
          job_text: state.data.jobIsUrl ? undefined : state.data.jobInput,
          job_url: state.data.jobIsUrl ? state.data.jobInput : undefined,
          resume_filename: resumeFilename,
        });
        setJobId(response.job_id);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        setStartError(msg);
      }
    })();
    // Only run once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- 2) Subscribe to the SSE stream ---
  const { state: jobState, isComplete, isFailed } = useProcessingJob(jobId);

  // --- 3) Track step transitions ---
  useEffect(() => {
    const current = jobState?.currentStep;
    if (!current) return;
    setStepLog((prev) => (prev[prev.length - 1] === current ? prev : [...prev, current]));
  }, [jobState?.currentStep]);

  // --- 4) Complete → hand the result off to the conversation context ---
  //
  // The `status=completed` event and the `done` event are two separate
  // messages; status can flip to "completed" BEFORE the `done` event
  // delivers the final `result` payload. So we wait for whichever comes
  // later, with a 1.5s safety net in case the backend never sends a
  // `result` (e.g., older server builds).
  const advancedRef = useRef(false);
  useEffect(() => {
    if (!isComplete || advancedRef.current) return;

    const completion = jobState?.result;
    if (!completion) {
      const grace = window.setTimeout(() => {
        setStartError('Optimization finished, but the final review payload has not arrived yet.');
      }, 1500);
      return () => window.clearTimeout(grace);
    }

    let cancelled = false;
    let revealTimeout: number | undefined;

    const finish = async () => {
      try {
        let review = completion.review;
        if (!review) {
          const applicationId = completion.applicationId;
          if (!applicationId) {
            throw new Error('Pipeline completed but application ID is missing.');
          }
          review = await getApplicationReview(applicationId);
        }

        if (cancelled) return;
        advancedRef.current = true;
        revealTimeout = window.setTimeout(() => {
          if (!cancelled) {
            completeProcessing(review);
          }
        }, 650);
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : 'Failed to load the final review.';
        setStartError(message);
      }
    };

    void finish();

    return () => {
      cancelled = true;
      if (revealTimeout !== undefined) {
        window.clearTimeout(revealTimeout);
      }
    };
  }, [isComplete, completeProcessing, jobState?.result]);

  // Latest insight for the ambient caption line under the active step.
  const latestInsight = jobState?.insights[0];
  const activeStep = stepLog[stepLog.length - 1];
  const historyBefore = stepLog.slice(0, Math.max(0, stepLog.length - 1));

  return (
    <div className="relative flex w-full flex-col items-center gap-4">
      {/* Background pulsing aura — visual anchor while the AI works. */}
      <ProcessingAura />

      {/* Prior step history — completed steps in past tense with a subtle
          check, each older entry fading progressively. */}
      <div className="flex w-full flex-col items-center gap-1.5">
        <AnimatePresence initial={false}>
          {historyBefore.map((name, i) => {
            // Older entries get progressively more muted.
            const depth = historyBefore.length - 1 - i;
            const opacity = Math.max(0.35, 0.85 - depth * 0.18);
            return (
              <motion.div
                key={name}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
                className="flex items-center gap-1.5 text-[14px] text-ink-500"
              >
                <Check
                  className="h-3.5 w-3.5 text-sky-400/80"
                  strokeWidth={2.5}
                  aria-hidden="true"
                />
                <span>{STEP_LABELS[name].done}</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Active step — glowing hero line, typewriter reveal. */}
      <div className="flex min-h-[4.5rem] w-full items-center justify-center">
        <AnimatePresence mode="wait" initial={false}>
          {activeStep ? (
            <ActiveStepLine key={activeStep} step={activeStep} />
          ) : (
            <motion.p
              key="warming"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-[20px] font-light text-ink-600"
            >
              {startError ? startError : 'Warming up the optimizer…'}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* Latest insight — small ambient caption under the active step. */}
      <div className="min-h-[1.5rem] w-full text-center">
        <AnimatePresence mode="wait">
          {latestInsight && (
            <motion.p
              key={latestInsight.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35 }}
              className={cn(
                'mx-auto max-w-[40ch] text-[13px] italic text-ink-500',
                latestInsight.importance === 'high' && 'text-ink-700',
              )}
            >
              {latestInsight.message}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {startError && !isFailed && (
        <p className="mt-1 text-[13px] text-red-500">{startError}</p>
      )}

      {isFailed && (
        <p className="mt-1 text-[13px] text-red-500">
          Something went wrong on the backend. Check the server logs and try again.
        </p>
      )}
    </div>
  );
}

/**
 * Hero line for the currently-executing step. Uses the same typewriter
 * reveal as regular agent messages plus a soft blue glow to communicate
 * "this is live and happening right now".
 */
function ActiveStepLine({ step }: { step: StepName }) {
  const text = STEP_LABELS[step].active;
  const { displayed, done } = useTypewriter(text, { speed: 22 });

  return (
    <motion.p
      initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: -6, filter: 'blur(3px)' }}
      transition={{ duration: 0.45, ease: [0.2, 0.7, 0.2, 1] }}
      className={cn(
        'mx-auto max-w-[44ch] text-center text-[24px] font-light leading-[1.28] tracking-[-0.01em]',
        'text-ink-900 sm:max-w-[52ch] sm:text-[28px]',
      )}
      style={{
        textShadow: '0 0 22px rgba(125, 170, 255, 0.35)',
      }}
      aria-label={text}
    >
      <span aria-hidden="true">{displayed}</span>
      <motion.span
        aria-hidden="true"
        animate={done ? { opacity: [0.4, 1, 0.4] } : { opacity: [0.2, 1, 0.2] }}
        transition={{ duration: done ? 1.4 : 1, repeat: Infinity, ease: 'easeInOut' }}
        className="ml-0.5 inline-block h-[0.95em] w-[2px] translate-y-[0.12em] rounded-sm bg-sky-400 align-baseline"
      />
    </motion.p>
  );
}

/**
 * Decorative radial glow that lives behind the stage while the AI is
 * working. Positioned absolutely inside the ProcessingStream wrapper.
 */
function ProcessingAura() {
  return (
    <motion.div
      aria-hidden="true"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/2"
    >
      <motion.div
        animate={{ scale: [1, 1.06, 1], opacity: [0.55, 0.85, 0.55] }}
        transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute inset-0 rounded-full"
        style={{
          background:
            'radial-gradient(circle at center, rgba(125, 170, 255, 0.45) 0%, rgba(200, 220, 255, 0.25) 35%, transparent 70%)',
          filter: 'blur(24px)',
        }}
      />
      <motion.div
        animate={{ scale: [1.05, 0.98, 1.05], opacity: [0.35, 0.7, 0.35] }}
        transition={{ duration: 4.6, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute inset-8 rounded-full"
        style={{
          background:
            'radial-gradient(circle at center, rgba(255, 255, 255, 0.55) 0%, transparent 60%)',
          filter: 'blur(18px)',
        }}
      />
    </motion.div>
  );
}
