import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from 'react';
import type {
  AgentMessage,
  ConversationState,
  Message,
  UserMessage,
} from './types';
import type { ApplicationReview } from '@/types/review';
import { useAuth } from '@/auth/AuthContext';
import {
  getLatestApplicationReview,
  refineResume as refineResumeApi,
} from '@/lib/api';
import { findStep, initialScript } from './script';

type Action =
  | { type: 'BOOT' }
  | { type: 'AGENT_TYPING'; value: boolean }
  | { type: 'PUSH_AGENT'; message: AgentMessage; stepId: string }
  | { type: 'PUSH_USER'; message: UserMessage }
  | { type: 'ADVANCE'; nextStepId: string | null; patch?: Record<string, unknown> }
  | { type: 'RESTORE_REVIEW'; review: ApplicationReview; message: AgentMessage }
  | { type: 'COMPLETE_PROCESSING'; review: ApplicationReview; message: AgentMessage }
  | { type: 'REFINE_START'; instruction: string }
  | { type: 'REFINE_SUCCESS'; review: ApplicationReview; message: AgentMessage }
  | { type: 'REFINE_ERROR'; error: string }
  | { type: 'RESET' };

const initialState: ConversationState = {
  phase: 'IDLE',
  messages: [],
  data: {},
  agentTyping: false,
};

function reducer(state: ConversationState, action: Action): ConversationState {
  switch (action.type) {
    case 'BOOT': {
      const first = initialScript[0];
      return {
        ...initialState,
        currentStepId: first.id,
        phase: first.phase,
      };
    }
    case 'AGENT_TYPING':
      return { ...state, agentTyping: action.value };
    case 'PUSH_AGENT': {
      return {
        ...state,
        messages: [...state.messages, action.message],
        activeAgentMessageId: action.message.id,
        currentStepId: action.stepId,
        agentTyping: false,
      };
    }
    case 'PUSH_USER': {
      return {
        ...state,
        messages: [...state.messages, action.message],
        // User answered, so previous agent message no longer owns the composer.
        activeAgentMessageId: undefined,
      };
    }
    case 'ADVANCE': {
      const mergedData = { ...state.data, ...(action.patch ?? {}) };
      if (action.nextStepId === null) {
        return { ...state, data: mergedData, currentStepId: undefined };
      }
      const next = findStep(action.nextStepId);
      return {
        ...state,
        data: mergedData,
        currentStepId: action.nextStepId,
        phase: next ? next.phase : state.phase,
      };
    }
    case 'REFINE_START': {
      return {
        ...state,
        refining: true,
        refineInstruction: action.instruction,
        refineError: undefined,
      };
    }
    case 'REFINE_SUCCESS': {
      return {
        ...state,
        refining: false,
        refineError: undefined,
        data: {
          ...state.data,
          review: action.review,
        },
        messages: [...state.messages, action.message],
        activeAgentMessageId: action.message.id,
      };
    }
    case 'REFINE_ERROR': {
      return {
        ...state,
        refining: false,
        refineError: action.error,
      };
    }
    case 'RESTORE_REVIEW': {
      return {
        ...initialState,
        data: {
          review: action.review,
        },
        messages: [action.message],
        activeAgentMessageId: action.message.id,
        currentStepId: 'reviewing',
        phase: 'REVIEWING',
        agentTyping: false,
      };
    }
    case 'COMPLETE_PROCESSING': {
      // Atomic transition from PROCESSING -> REVIEWING: merge the result
      // into data AND push the final agent message in one dispatch so
      // the auto-emit effect doesn't race with a second prompt.
      const reviewStep = findStep('reviewing');
      return {
        ...state,
        data: {
          ...state.data,
          review: action.review,
        },
        messages: [...state.messages, action.message],
        activeAgentMessageId: action.message.id,
        currentStepId: 'reviewing',
        phase: reviewStep ? reviewStep.phase : 'REVIEWING',
        agentTyping: false,
      };
    }
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}

export interface ConversationApi {
  state: ConversationState;
  /** Active agent message (the one currently owning the composer). */
  activeAgent?: AgentMessage;
  /** Submit the user's reply from the composer. */
  submit: (input: { text: string; choiceValue?: string; file?: File | null }) => void;
  /**
   * Phase 5: called by <ProcessingStream/> once the SSE `done` event
   * lands. Transitions phase -> REVIEWING, merges the result payload
   * into `data`, and pushes the reveal message (summary list + closing).
   */
  completeProcessing: (review: ApplicationReview) => void;
  /**
   * Directly restore a previous application review (used when loading from history).
   */
  loadReview: (review: ApplicationReview) => void;
  /**
   * Phase 5 refinement: user submitted a free-form tweak instruction
   * from the composer. Locks the composer, shows the refining UI, then
   * replaces the review payload with the refined version on success.
   */
  refine: (instruction: string) => void;
  reset: () => void;
}

const Ctx = createContext<ConversationApi | null>(null);

function makeId(prefix: string) {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export const ConversationProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { isAuthenticated, loading: authLoading } = useAuth();
  const bootedRef = useRef(false);
  const skipRestoreRef = useRef(false);

  // Boot once on mount. If an authenticated user has a completed review,
  // restore directly into review mode; otherwise start the normal script.
  useEffect(() => {
    if (authLoading) return;
    if (bootedRef.current) return;
    bootedRef.current = true;
    let cancelled = false;
    let settled = false;

    void (async () => {
      if (!skipRestoreRef.current && isAuthenticated) {
        try {
          const review = await getLatestApplicationReview();
          if (cancelled) return;
          if (review) {
            settled = true;
            dispatch({
              type: 'RESTORE_REVIEW',
              review,
              message: buildReviewRestoreMessage(review),
            });
            return;
          }
        } catch (err) {
          if (cancelled) return;
          console.warn('Latest review restore failed; starting a new conversation.', err);
        }
      }

      if (!cancelled) {
        settled = true;
        dispatch({ type: 'BOOT' });
      }
    })();

    return () => {
      cancelled = true;
      if (!settled) {
        bootedRef.current = false;
      }
    };
  }, [authLoading, isAuthenticated]);

  // Whenever currentStepId changes but the latest message isn't from that
  // step's agent prompt, emit it (with a short typing delay for polish).
  useEffect(() => {
    const step = findStep(state.currentStepId);
    if (!step) return;
    const last = state.messages[state.messages.length - 1];
    const alreadyEmitted =
      last && last.role === 'agent' && last.stepId === step.id;
    if (alreadyEmitted) return;

    let cancelled = false;
    dispatch({ type: 'AGENT_TYPING', value: true });
    const delay = state.messages.length === 0 ? 250 : 550;
    const t = window.setTimeout(() => {
      if (cancelled) return;
      const msg: AgentMessage = {
        id: makeId('agent'),
        role: 'agent',
        text: step.message(state.data),
        ui: step.ui,
        stepId: step.id,
        createdAt: Date.now(),
      };
      dispatch({ type: 'PUSH_AGENT', message: msg, stepId: step.id });
    }, delay);

    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
    // We intentionally depend only on currentStepId; data changes during
    // a single step should not re-emit the prompt.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.currentStepId]);

  const submit = useCallback<ConversationApi['submit']>(
    (input) => {
      const step = findStep(state.currentStepId);
      if (!step) return;

      const isFileStep = step.ui.kind === 'file';

      // Compose a user message for the transcript.
      const humanText =
        input.choiceValue !== undefined
          ? labelForChoice(step, input.choiceValue) ?? input.text
          : isFileStep && input.file
            ? input.file.name
            : input.text;

      const userMsg: UserMessage = {
        id: makeId('user'),
        role: 'user',
        text: humanText || (input.file ? input.file.name : ''),
        choiceValue: input.choiceValue,
        attachment: input.file
          ? { name: input.file.name, size: input.file.size, mime: input.file.type }
          : undefined,
        createdAt: Date.now(),
      };

      // Nothing to echo? Still advance, but skip the empty bubble.
      if (userMsg.text || userMsg.attachment) {
        dispatch({ type: 'PUSH_USER', message: userMsg });
      }

      const { patch, nextStepId } = step.handle(input, state.data);
      dispatch({ type: 'ADVANCE', nextStepId, patch });
    },
    [state.currentStepId, state.data],
  );

  const reset = useCallback(() => {
    skipRestoreRef.current = true;
    bootedRef.current = false;
    dispatch({ type: 'RESET' });
    // Re-boot on the next tick so the BOOT effect reruns.
    window.setTimeout(() => {
      bootedRef.current = true;
      dispatch({ type: 'BOOT' });
    }, 0);
  }, []);

  // Keep a ref to the latest review so `refine` doesn't need to be
  // recreated (and fire a re-render) every time the review payload
  // changes. The callback only reads the current value at call-time.
  const reviewRef = useRef<ApplicationReview | undefined>(state.data.review);
  reviewRef.current = state.data.review;

  const refine = useCallback<ConversationApi['refine']>((instruction) => {
    const trimmed = instruction.trim();
    if (!trimmed) return;
    const current = reviewRef.current;
    if (!current) return;

    // Echo the user's instruction into the transcript so the chat
    // history reads as a natural back-and-forth.
    const userMsg: UserMessage = {
      id: makeId('user'),
      role: 'user',
      text: trimmed,
      createdAt: Date.now(),
    };
    dispatch({ type: 'PUSH_USER', message: userMsg });
    dispatch({ type: 'REFINE_START', instruction: trimmed });

    void (async () => {
      try {
        const updated = await refineResumeApi({
          applicationId: current.application_id,
          instruction: trimmed,
          current,
        });
        const points = updated.summary_points ?? [];
        const message: AgentMessage = {
          id: makeId('agent'),
          role: 'agent',
          text: 'Done — here\u2019s the updated version with your note applied.',
          body: {
            summaryPoints: points,
            closing:
              'Want to keep tweaking, or grab the file?',
          },
          ui: { kind: 'review' },
          stepId: 'reviewing',
          createdAt: Date.now(),
        };
        dispatch({ type: 'REFINE_SUCCESS', review: updated, message });
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : 'Refinement failed — try again.';
        dispatch({ type: 'REFINE_ERROR', error: msg });
      }
    })();
  }, []);

  const completeProcessing = useCallback<ConversationApi['completeProcessing']>(
    (review) => {
      const points = review.summary_points ?? [];
      const message: AgentMessage = {
        id: makeId('agent'),
        role: 'agent',
        text: "All done! I've completely revamped your profile. Here are the main things I focused on:",
        body: {
          summaryPoints: points,
          closing:
            'How does it look? We can keep tweaking it, or you can grab the file now.',
        },
        ui: { kind: 'review' },
        stepId: 'reviewing',
        createdAt: Date.now(),
      };
      dispatch({ type: 'COMPLETE_PROCESSING', review, message });
    },
    [],
  );

  const loadReview = useCallback<ConversationApi['loadReview']>((review) => {
    dispatch({
      type: 'RESTORE_REVIEW',
      review,
      message: buildReviewRestoreMessage(review),
    });
  }, []);

  const activeAgent = useMemo<AgentMessage | undefined>(() => {
    if (!state.activeAgentMessageId) return undefined;
    const found = state.messages.find(
      (m): m is AgentMessage =>
        m.role === 'agent' && m.id === state.activeAgentMessageId,
    );
    return found;
  }, [state.activeAgentMessageId, state.messages]);

  const value = useMemo<ConversationApi>(
    () => ({ state, activeAgent, submit, completeProcessing, loadReview, refine, reset }),
    [state, activeAgent, submit, completeProcessing, loadReview, refine, reset],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
};

export function useConversation(): ConversationApi {
  const ctx = useContext(Ctx);
  if (!ctx) {
    throw new Error('useConversation must be used within <ConversationProvider>');
  }
  return ctx;
}

// ——— helpers ———

function labelForChoice(
  step: ReturnType<typeof findStep>,
  value: string,
): string | undefined {
  if (!step) return undefined;
  if (step.ui.kind !== 'choices') return undefined;
  return step.ui.choices.find((c) => c.value === value)?.label;
}

// Re-exported for convenience in feed/components.
export type { Message };

function buildReviewRestoreMessage(review: ApplicationReview): AgentMessage {
  return {
    id: makeId('agent'),
    role: 'agent',
    text: "Welcome back — here's your latest optimized resume.",
    body: {
      summaryPoints: review.summary_points ?? [],
      closing:
        'Want to keep tweaking, or grab the file?',
    },
    ui: { kind: 'review' },
    stepId: 'reviewing',
    createdAt: Date.now(),
  };
}
