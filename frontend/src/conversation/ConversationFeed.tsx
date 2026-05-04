import { AnimatePresence } from 'framer-motion';
import { useConversation } from './ConversationContext';
import { AgentTypingIndicator, MessageBubble, RefiningIndicator } from './MessageBubble';
import { ProcessingStream } from './ProcessingStream';
import { cn } from '@/lib/cn';

/**
 * Single-turn stage. Only the active agent message is shown at a time —
 * previous turns are not rendered here (their captured data is surfaced
 * via the <ContextStrip/>).
 *
 * Phase-specific behavior:
 *   - PROCESSING →  <ProcessingStream/> owns the stage.
 *   - REVIEWING  →  content flows top-down inside the left column (the
 *                   message body is tall: hero + list + closing).
 *   - otherwise  →  content is vertically centered on the stage.
 */
export function ConversationFeed() {
  const { state, activeAgent } = useConversation();

  if (state.phase === 'PROCESSING') {
    return (
      <section
        aria-live="polite"
        className="relative flex min-h-[12rem] w-full items-center justify-center"
      >
        <ProcessingStream />
      </section>
    );
  }

  // Prefer typing dots whenever we're between turns (activeAgent may be
  // momentarily undefined after a user reply while the next step prepares).
  const showTyping = state.agentTyping || !activeAgent;
  const isReviewing = state.phase === 'REVIEWING';
  const isRefining = !!state.refining;

  return (
    <section
      aria-live="polite"
      className={cn(
        'flex w-full',
        isReviewing
          ? 'min-h-[8rem] items-start justify-start'
          : 'min-h-[8rem] items-center justify-center',
      )}
    >
      <AnimatePresence mode="wait" initial={false}>
        {isRefining ? (
          <RefiningIndicator
            key="refining"
            instruction={state.refineInstruction ?? ''}
          />
        ) : showTyping ? (
          <AgentTypingIndicator key="typing" />
        ) : (
          <MessageBubble
            key={activeAgent!.id}
            message={activeAgent!}
            isLatest
          />
        )}
      </AnimatePresence>
    </section>
  );
}
