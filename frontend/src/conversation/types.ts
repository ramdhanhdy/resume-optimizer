// Core conversation types shared by the context, feed, and script engine.

import type { ApplicationReview } from '@/types/review';

export type Phase =
  | 'IDLE'
  | 'GATHERING_INFO'
  | 'AUTH_GATE'
  | 'PROCESSING'
  | 'REVIEWING';

/**
 * A single choice rendered as a floating pill above the input bar.
 * `value` is what flows into state; `label` is what the user sees.
 */
export interface Choice {
  value: string;
  label: string;
  hint?: string;
}

/**
 * The shape of contextual UI an agent message wants to expose.
 * When a message has `ui: undefined`, the composer falls back to the free-form
 * text input. Only one message at a time should carry a non-null `ui`.
 */
export type AgentUI =
  | { kind: 'text'; placeholder?: string; multiline?: boolean }
  | { kind: 'choices'; choices: Choice[]; allowFreeText?: boolean; placeholder?: string }
  | { kind: 'file'; accept?: string; placeholder?: string; allowFreeText?: boolean }
  | { kind: 'auth'; providers: Array<'google' | 'email'> }
  /**
   * Phase 5 reveal state. No composer input; the AgentMessage's body
   * describes the summary list and the Composer renders <ReviewActions/>
   * (download + tweak pills) instead of a text field.
   */
  | { kind: 'review' }
  | { kind: 'none' };

/**
 * Optional structured content rendered below the agent's hero line. Used
 * by the Phase 5 reveal message, which needs a styled summary list plus
 * a separate closing paragraph.
 */
export interface AgentMessageBody {
  summaryPoints?: string[];
  closing?: string;
}

export interface AgentMessage {
  id: string;
  role: 'agent';
  text: string;
  /** Optional rich body rendered below `text` (Phase 5 summary list). */
  body?: AgentMessageBody;
  /** Contextual UI module this message is asking the user for. */
  ui?: AgentUI;
  /** Identifier of the script step that produced this message. */
  stepId?: string;
  createdAt: number;
}

export interface UserMessage {
  id: string;
  role: 'user';
  text: string;
  /** If the user answered via a choice pill, we keep the value here too. */
  choiceValue?: string;
  /** If a file was attached. */
  attachment?: {
    name: string;
    size: number;
    mime: string;
  };
  createdAt: number;
}

export type Message = AgentMessage | UserMessage;

/**
 * All data the conversation gathers before hitting the optimize backend.
 * Keep this loose so new script steps can write arbitrary keys without
 * a type migration; use the helpers in `ConversationContext` to read safely.
 */
export interface CollectedData {
  resumeFile?: { name: string; size: number; mime: string; file?: File };
  resumeText?: string;
  jobInput?: string; // raw job description text or URL
  jobIsUrl?: boolean;
  additionalProfileFile?: { name: string; size: number; mime: string; file?: File };
  additionalProfileText?: string;
  saveResume?: boolean;
  linkedinUrl?: string;
  githubUsername?: string;
  forceRefreshProfile?: boolean;
  /** Phase 5: canonical review payload returned by the backend. */
  review?: ApplicationReview;
  [key: string]: unknown;
}

export interface ConversationState {
  phase: Phase;
  messages: Message[];
  /** Id of the most recent agent message that still owns the composer. */
  activeAgentMessageId?: string;
  data: CollectedData;
  /** Script engine cursor; undefined means "script not running". */
  currentStepId?: string;
  /** Transient flag while the "agent is typing" indicator is shown. */
  agentTyping: boolean;
  /**
   * Phase 5: true while a user-initiated refinement is in-flight.
   * Drives the muted typewriter line in the chat column, the shimmer
   * overlay on the resume stage, and the locked composer state.
   */
  refining?: boolean;
  /** Last instruction the user submitted during a refinement. */
  refineInstruction?: string;
  /** Transient error message if a refinement request failed. */
  refineError?: string;
}
