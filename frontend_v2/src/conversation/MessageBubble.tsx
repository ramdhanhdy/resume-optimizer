import { motion, useReducedMotion } from 'framer-motion';
import { FileText } from 'lucide-react';
import type { AgentMessageBody, Message } from './types';
import { useTypewriter } from './useTypewriter';
import { cn } from '@/lib/cn';

interface MessageBubbleProps {
  message: Message;
  /**
   * True for the most recent message in the feed. The latest agent turn
   * renders as Gemini-style hero typography; older turns fade back into
   * muted history prose.
   */
  isLatest?: boolean;
}

/**
 * Typography-first turn rendering. No avatar, no container chrome.
 *   - Agent + latest  → centered hero text (large, light weight)
 *   - Agent + older   → muted prose (smaller, ink-500)
 *   - User            → right-aligned, subtle sky tint
 */
export function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  if (message.role === 'agent') {
    if (isLatest) {
      // Review messages (with a `body`) flow top-down, left-aligned, so
      // the hero + list + closing read as a single editorial column.
      // Everything else stays Gemini-style centered.
      const isReview = !!message.body;
      return (
        <div
          className={cn(
            'flex w-full flex-col gap-5',
            isReview ? 'items-start' : 'items-center',
          )}
        >
          <HeroAgentLine text={message.text} align={isReview ? 'left' : 'center'} />
          {message.body && <AgentRichBody body={message.body} />}
        </div>
      );
    }
    return (
      <motion.p
        layout
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className={cn(
          'mx-auto w-full max-w-[44ch] text-center',
          'text-[16px] leading-relaxed text-ink-500',
        )}
      >
        {message.text}
      </motion.p>
    );
  }

  // User turn — right-aligned soft pill.
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="flex w-full justify-end"
    >
      <div
        className={cn(
          'max-w-[52ch] rounded-[22px] px-4 py-2 text-[15px] leading-relaxed',
          'bg-sky-100/70 text-ink-800 ring-1 ring-sky-200/60',
          !isLatest && 'bg-sky-100/40 text-ink-500 ring-sky-200/40',
        )}
      >
        {message.attachment && (
          <span className="mb-1 inline-flex items-center gap-1.5 rounded-full bg-white/70 px-2 py-0.5 text-xs text-ink-500">
            <FileText className="h-3 w-3" strokeWidth={2} />
            {message.attachment.name}
          </span>
        )}
        {message.text && <div>{message.text}</div>}
      </div>
    </motion.div>
  );
}

/**
 * Hero agent line with per-character typewriter reveal. A soft caret
 * pulses at the end of the visible text until the reveal completes,
 * then fades out.
 *
 * `align='center'` is the Gemini-style centered hero used throughout the
 * gathering phases. `align='left'` is used by the Phase 5 review message,
 * where the hero is one piece of a larger editorial column (list +
 * closing) that all left-aligns together.
 */
function HeroAgentLine({
  text,
  align = 'center',
}: {
  text: string;
  align?: 'center' | 'left';
}) {
  const reduce = useReducedMotion();
  const { displayed, done } = useTypewriter(text, { speed: 20, enabled: !reduce });

  return (
    <motion.p
      initial={{ opacity: 0, y: 14, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.5, ease: [0.2, 0.7, 0.2, 1] }}
      className={cn(
        'w-full font-light leading-[1.28] tracking-[-0.01em] text-ink-800',
        align === 'center'
          ? 'mx-auto max-w-[40ch] text-center text-[26px] sm:max-w-[48ch] sm:text-[30px]'
          : // Left-aligned review hero: slightly smaller so the list
            // below doesn't feel visually overshadowed.
            'text-left text-[22px] sm:text-[24px]',
      )}
      // Let screen readers announce the final sentence, not every keystroke.
      aria-label={text}
    >
      <span aria-hidden="true">{displayed}</span>
      <motion.span
        aria-hidden="true"
        animate={
          reduce
            ? { opacity: done ? 0 : 1 }
            : done
              ? { opacity: 0 }
              : { opacity: [0.2, 1, 0.2] }
        }
        transition={
          reduce
            ? { duration: 0.15, ease: 'easeOut' }
            : done
              ? { duration: 0.35, ease: 'easeOut' }
              : { duration: 1, repeat: Infinity, ease: 'easeInOut' }
        }
        className="ml-0.5 inline-block h-[0.95em] w-[2px] translate-y-[0.12em] rounded-sm bg-sky-400 align-baseline"
      />
    </motion.p>
  );
}

/**
 * Phase 5 rich body: a styled summary list plus an optional closing line.
 * Rendered below the hero text when an agent message carries `body`.
 * Staggers in so the list points arrive one at a time after the hero has
 * finished typing.
 */
function AgentRichBody({ body }: { body: AgentMessageBody }) {
  const points = body.summaryPoints ?? [];
  return (
    <motion.div
      className="flex w-full flex-col items-start gap-5"
    >
      {points.length > 0 && (
        <ul className="flex w-full flex-col gap-2 text-left">
          {points.map((point, i) => (
            <motion.li
              key={point}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                delay: 0.4 + i * 0.12,
                duration: 0.4,
                ease: 'easeOut',
              }}
              className={cn(
                'flex items-start gap-3 text-[15px] leading-relaxed text-ink-700',
                'sm:text-[16px]',
              )}
            >
              <span
                aria-hidden="true"
                className="mt-[0.55em] block h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400"
              />
              <span>{point}</span>
            </motion.li>
          ))}
        </ul>
      )}
      {body.closing && (
        <motion.p
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.4 + points.length * 0.12 + 0.15,
            duration: 0.45,
            ease: 'easeOut',
          }}
          className={cn(
            'w-full text-left text-[16px] leading-relaxed text-ink-700',
            'sm:text-[17px]',
          )}
        >
          {body.closing}
        </motion.p>
      )}
    </motion.div>
  );
}

/**
 * "Agent is thinking" indicator — three gently pulsing sky dots, centered
 * so it sits on the same axis as the hero prose.
 */
export function AgentTypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex w-full items-center justify-center gap-1.5"
    >
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="block h-1.5 w-1.5 rounded-full bg-sky-300"
          animate={{ opacity: [0.25, 1, 0.25], y: [0, -2, 0] }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.15,
            ease: 'easeInOut',
          }}
        />
      ))}
    </motion.div>
  );
}
