import type { AgentUI, CollectedData, Phase } from './types';

/**
 * A script step describes one prompt/response turn driven by the agent.
 * `next()` returns the id of the next step (or `null` to end the script),
 * and optionally bumps the global phase.
 */
export interface ScriptStep {
  id: string;
  /** The phase to enter WHEN this step is activated. */
  phase: Phase;
  /** Agent's message text. Can reference already-collected fields. */
  message: (data: CollectedData) => string;
  /** Contextual UI module to render for this step. */
  ui: AgentUI;
  /**
   * Handle the user's answer. Should return a patch to merge into
   * `CollectedData`, plus the id of the next step.
   * Return `nextStepId: null` to end the gathering phase.
   */
  handle: (
    input: { text: string; choiceValue?: string; file?: File | null },
    data: CollectedData,
  ) => { patch?: Partial<CollectedData>; nextStepId: string | null };
}

/**
 * Minimal end-to-end gathering script for Phase 1/2. Later phases
 * (AUTH_GATE, PROCESSING, REVIEWING) can be appended by adding steps.
 */
export const initialScript: ScriptStep[] = [
  {
    id: 'welcome',
    phase: 'IDLE',
    message: () =>
      "Hi — I'm your resume co-pilot. In a minute, I'll rewrite your resume for a specific job. Ready to start?",
    ui: {
      kind: 'choices',
      choices: [
        { value: 'start', label: "Let's go" },
        { value: 'tell_more', label: 'Tell me more first' },
      ],
    },
    handle: (input) => {
      if (input.choiceValue === 'tell_more') {
        return { nextStepId: 'explainer' };
      }
      return { nextStepId: 'ask_resume' };
    },
  },
  {
    id: 'explainer',
    phase: 'IDLE',
    message: () =>
      "I'll ask for your resume and the job you're targeting, tailor bullet points for ATS and impact, and hand you a polished .docx. You stay in control — nothing is sent until you approve.",
    ui: {
      kind: 'choices',
      choices: [{ value: 'start', label: 'Got it — start' }],
    },
    handle: () => ({ nextStepId: 'ask_resume' }),
  },
  {
    id: 'ask_resume',
    phase: 'GATHERING_INFO',
    message: () =>
      "Let's start with your resume. Drop in a PDF or DOCX, or paste the text below.",
    ui: {
      kind: 'file',
      accept: '.pdf,.docx,.txt,.md',
      placeholder: 'or paste your resume text here…',
      allowText: true,
    },
    handle: (input) => {
      const patch: Partial<CollectedData> = {};
      if (input.file) {
        patch.resumeFile = {
          name: input.file.name,
          size: input.file.size,
          mime: input.file.type,
        };
      }
      if (input.text && input.text.trim().length > 0) {
        patch.resumeText = input.text.trim();
      }
      return { patch, nextStepId: 'ask_job' };
    },
  },
  {
    id: 'ask_job',
    phase: 'GATHERING_INFO',
    message: () =>
      'Now the target role. Paste the job description or a link to the posting.',
    ui: {
      kind: 'text',
      placeholder: 'Paste the job description or URL…',
      multiline: true,
    },
    handle: (input) => {
      const text = input.text.trim();
      const isUrl = /^https?:\/\//i.test(text);
      return {
        patch: { jobInput: text, jobIsUrl: isUrl },
        nextStepId: 'ask_level',
      };
    },
  },
  {
    id: 'ask_level',
    phase: 'GATHERING_INFO',
    message: () => 'How should I pitch your experience level?',
    ui: {
      kind: 'choices',
      choices: [
        { value: 'junior', label: 'Junior', hint: '0–2 yrs' },
        { value: 'mid', label: 'Mid-level', hint: '3–5 yrs' },
        { value: 'senior', label: 'Senior', hint: '6–9 yrs' },
        { value: 'lead', label: 'Lead / Staff', hint: '10+ yrs' },
      ],
    },
    handle: (input) => ({
      patch: {
        experienceLevel: (input.choiceValue as CollectedData['experienceLevel']) ?? 'mid',
      },
      nextStepId: 'ask_tone',
    }),
  },
  {
    id: 'ask_tone',
    phase: 'GATHERING_INFO',
    message: () => 'What tone should the final resume strike?',
    ui: {
      kind: 'choices',
      choices: [
        { value: 'concise', label: 'Concise', hint: 'punchy, action-led' },
        { value: 'balanced', label: 'Balanced', hint: 'default' },
        { value: 'detailed', label: 'Detailed', hint: 'richer context' },
      ],
    },
    handle: (input) => ({
      patch: {
        tonePreference: (input.choiceValue as CollectedData['tonePreference']) ?? 'balanced',
      },
      // End of Phase 1/2 gathering; AUTH_GATE/PROCESSING come in later phases.
      nextStepId: 'auth_gate',
    }),
  },
  {
    id: 'auth_gate',
    phase: 'AUTH_GATE',
    message: () =>
      "Great, I have what I need. Sign in quickly and I'll securely save your documents before I start optimizing.",
    ui: {
      kind: 'auth',
      providers: ['google'],
    },
    // Advancing is driven by <AuthGateBridge/> once `isAuthenticated` flips.
    handle: () => ({ nextStepId: 'processing' }),
  },
  {
    id: 'processing',
    phase: 'PROCESSING',
    // The <ProcessingStream/> replaces the hero line while this step is
    // active, so this `message` only shows for a split second during the
    // phase transition. Keep it short and calming.
    message: () => "Alright — optimizing now.",
    ui: { kind: 'none' },
    handle: () => ({ nextStepId: 'reviewing' }),
  },
  {
    id: 'reviewing',
    phase: 'REVIEWING',
    message: () =>
      "All done — here's the optimized draft. Phase 5 will surface the diff view here.",
    ui: { kind: 'none' },
    handle: () => ({ nextStepId: null }),
  },
];

export function findStep(id: string | undefined): ScriptStep | undefined {
  if (!id) return undefined;
  return initialScript.find((s) => s.id === id);
}
