import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  InsightState,
  ProcessingEvent,
  ProcessingJobState,
  StepName,
  StepState,
} from '@/types/streaming';
import type { ApplicationReview } from '@/types/review';
import { STEP_ORDER } from '@/types/streaming';
import { supabase } from '@/lib/supabase';
import { API_BASE_URL, MOCK_STREAM } from '@/lib/api';

/**
 * Subscribe to the SSE stream for a processing job. Mirrors the legacy
 * `frontend/src/hooks/useProcessingJob.ts` with two additions:
 *   1. A scripted `MOCK_STREAM` mode for developing the UI without a live
 *      backend (enable with `VITE_MOCK_STREAM=true`).
 *   2. Graceful no-op when `jobId` is null (e.g. while the pipeline start
 *      request is still in flight).
 */

function initializeSteps(): StepState[] {
  return STEP_ORDER.map((name) => ({
    name,
    progress: 0,
    status: 'pending' as const,
  }));
}

export function useProcessingJob(jobId: string | null) {
  const [state, setState] = useState<ProcessingJobState | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastEventTsRef = useRef<number>(Date.now());

  // Initialize state when jobId changes.
  useEffect(() => {
    if (!jobId) {
      setState(null);
      return;
    }
    setState({
      jobId,
      status: 'started',
      steps: initializeSteps(),
      insights: [],
      metrics: {},
      validations: [],
      connection: {
        connected: false,
        lagMs: 0,
        lastEventTs: Date.now(),
      },
    });
  }, [jobId]);

  // Handle incoming events.
  const handleEvent = useCallback((event: ProcessingEvent) => {
    lastEventTsRef.current = Date.now();

    setState((prev) => {
      if (!prev) return prev;
      const next = { ...prev };

      switch (event.type) {
        case 'job_status':
          next.status = event.payload.status;
          break;

        case 'step_progress': {
          const { step, pct, eta_sec } = event.payload;
          next.currentStep = step;
          const now = Date.now();
          next.steps = prev.steps.map((s) => {
            if (s.name === step) {
              const isStarting = s.status === 'pending' && pct > 0;
              const isCompleting = pct === 100 && s.status !== 'completed';
              return {
                ...s,
                progress: pct,
                eta_sec,
                status: pct === 100 ? 'completed' : 'in_progress',
                startedAt: isStarting ? now : s.startedAt,
                completedAt: isCompleting ? now : s.completedAt,
              };
            }
            const stepIndex = STEP_ORDER.indexOf(s.name);
            const currentIndex = STEP_ORDER.indexOf(step);
            if (stepIndex < currentIndex && s.status !== 'completed') {
              return {
                ...s,
                progress: 100,
                status: 'completed',
                completedAt: s.completedAt ?? now,
              };
            }
            return s;
          });
          break;
        }

        case 'insight_emitted': {
          const insight: InsightState = {
            id: event.payload.id,
            category: event.payload.category,
            importance: event.payload.importance,
            message: event.payload.message,
            step: event.payload.step,
            ts: event.ts,
          };
          next.insights = [insight, ...prev.insights].slice(0, 20);
          break;
        }

        case 'metric_update': {
          const { key, value, unit } = event.payload;
          next.metrics = { ...prev.metrics, [key]: { key, value, unit } };
          if (key === 'application_id') next.applicationId = value;
          break;
        }

        case 'validation_update': {
          const v = event.payload;
          const idx = prev.validations.findIndex((x) => x.rule_id === v.rule_id);
          if (idx >= 0) {
            next.validations = [...prev.validations];
            next.validations[idx] = v;
          } else {
            next.validations = [...prev.validations, v];
          }
          break;
        }

        case 'error':
          next.connection = { ...prev.connection, error: event.payload.message };
          break;

        case 'heartbeat':
          next.connection = {
            ...prev.connection,
            lagMs: Date.now() - event.ts,
            lastEventTs: event.ts,
          };
          break;

        case 'done': {
          if (prev.status !== 'failed' && prev.status !== 'canceled') {
            next.status = 'completed';
          }
          const applicationId = event.payload.application_id ?? prev.applicationId;
          if (event.payload.application_id) {
            next.applicationId = event.payload.application_id;
          }
          next.result = {
            applicationId,
            reviewUrl: event.payload.review_url,
            review: event.payload.review,
          };
          break;
        }
      }

      return next;
    });
  }, []);

  // Real SSE connection OR scripted mock stream.
  useEffect(() => {
    if (!jobId) return;

    if (MOCK_STREAM) {
      return runMockStream(jobId, handleEvent);
    }

    let cancelled = false;
    let es: EventSource | null = null;

    (async () => {
      let streamUrl = `${API_BASE_URL}/api/jobs/${jobId}/stream`;
      // EventSource can't set headers, so pass the token as a query param.
      if (supabase) {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (session?.access_token) {
          streamUrl += `?access_token=${encodeURIComponent(session.access_token)}`;
        }
      }
      if (cancelled) return;

      es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setState((prev) =>
          prev
            ? {
                ...prev,
                connection: { ...prev.connection, connected: true, error: undefined },
              }
            : prev,
        );
      };

      es.onmessage = (e) => {
        try {
          handleEvent(JSON.parse(e.data) as ProcessingEvent);
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error('Failed to parse SSE event:', err);
        }
      };

      es.onerror = () => {
        setState((prev) =>
          prev
            ? {
                ...prev,
                connection: {
                  ...prev.connection,
                  connected: false,
                  error: 'Connection lost',
                },
              }
            : prev,
        );
      };
    })();

    return () => {
      cancelled = true;
      es?.close();
      eventSourceRef.current = null;
    };
  }, [jobId, handleEvent]);

  return {
    state,
    isConnected: state?.connection.connected ?? false,
    isComplete: state?.status === 'completed',
    isFailed: state?.status === 'failed',
  };
}

/**
 * Emits a scripted SSE-shaped event timeline so Phase 4 UI can be
 * developed + demoed without hitting the real backend. Returns a
 * cleanup function.
 */
function runMockStream(
  jobId: string,
  emit: (e: ProcessingEvent) => void,
): () => void {
  const timeouts: number[] = [];
  const schedule = (ms: number, fn: () => void) => {
    timeouts.push(window.setTimeout(fn, ms));
  };

  const stepFor = (step: StepName, startMs: number, durationMs: number) => {
    schedule(startMs, () =>
      emit({
        type: 'step_progress',
        ts: Date.now(),
        job_id: jobId,
        payload: { step, pct: 10 },
      }),
    );
    schedule(startMs + durationMs * 0.5, () =>
      emit({
        type: 'step_progress',
        ts: Date.now(),
        job_id: jobId,
        payload: { step, pct: 55, eta_sec: Math.round(durationMs / 1000 / 2) },
      }),
    );
    schedule(startMs + durationMs, () =>
      emit({
        type: 'step_progress',
        ts: Date.now(),
        job_id: jobId,
        payload: { step, pct: 100 },
      }),
    );
  };

  // Initial status
  schedule(100, () =>
    emit({
      type: 'job_status',
      ts: Date.now(),
      job_id: jobId,
      payload: { status: 'running' },
    }),
  );

  stepFor('analyzing', 300, 1400);
  schedule(1000, () =>
    emit({
      type: 'insight_emitted',
      ts: Date.now(),
      job_id: jobId,
      payload: {
        id: 'ins-1',
        category: 'experience',
        importance: 'medium',
        message: 'Strong signal in distributed systems and observability.',
        step: 'analyzing',
      },
    }),
  );

  stepFor('planning', 1800, 1400);
  stepFor('writing', 3300, 2200);
  schedule(4500, () =>
    emit({
      type: 'insight_emitted',
      ts: Date.now(),
      job_id: jobId,
      payload: {
        id: 'ins-2',
        category: 'impact',
        importance: 'high',
        message: 'Rewrote 4 bullets to lead with quantified outcomes.',
        step: 'writing',
      },
    }),
  );

  stepFor('validating', 5600, 1200);
  stepFor('polishing', 6900, 1100);

  schedule(8100, () =>
    emit({
      type: 'job_status',
      ts: Date.now(),
      job_id: jobId,
      payload: { status: 'completed' },
    }),
  );
  schedule(8200, () =>
    emit({
      type: 'done',
      ts: Date.now(),
      job_id: jobId,
      payload: {
        application_id: 1,
        review: buildMockReview(),
      },
    }),
  );

  return () => {
    timeouts.forEach((id) => window.clearTimeout(id));
  };
}

/**
 * Plain-text "optimized resume" rendered on the stage when MOCK_STREAM
 * is active. Intentionally terse + generic so it reads as a real doc
 * preview without pretending to match any specific input.
 */
function buildMockReview(): ApplicationReview {
  return {
    application_id: 1,
    status: 'completed',
    resume: {
      filename: 'optimized-resume.docx',
      plain_text: MOCK_RESUME_PREVIEW,
      markdown: MOCK_RESUME_PREVIEW,
    },
    summary_points: [
      'Rewrote your summary to lead with distributed-systems leadership',
      'Injected quantified impact metrics across four experience bullets',
      'Restructured the Experience section for ATS-friendly parsing',
      'Aligned skills and keywords with the job description',
    ],
    exports: {},
  };
}

const MOCK_RESUME_PREVIEW = `ALEX MORGAN
Senior Software Engineer · Distributed Systems

SUMMARY
────────────────────────────────────────────
Platform-minded engineer with 8+ years leading reliability and
observability efforts across multi-region services. Shipped
infrastructure that reduced p99 latency by 38% and cut on-call
pages in half while scaling the team from 4 to 11.

EXPERIENCE
────────────────────────────────────────────
TechCorp — Staff Engineer, Platform               2021 — Present
 • Led a 6-engineer team rewriting the ingestion pipeline, moving
   2.4B daily events to a tiered Kafka + ClickHouse architecture.
 • Reduced p99 read latency by 38% and cut infra spend by $420k/yr.
 • Authored the org-wide incident-review playbook now used by
   14 teams; mean-time-to-resolution improved 27% YoY.

Flux Labs — Senior Engineer                       2018 — 2021
 • Designed the observability stack powering 90+ microservices;
   on-call burden dropped from 12 → 5 pages/engineer/week.
 • Mentored 4 engineers to promotion; ran the internal
   "distributed systems" reading group.

SKILLS
────────────────────────────────────────────
Go · Rust · Kafka · ClickHouse · Kubernetes · OpenTelemetry
PostgreSQL · AWS · Terraform · gRPC

EDUCATION
────────────────────────────────────────────
B.S. Computer Science — University of Washington, 2016`;
