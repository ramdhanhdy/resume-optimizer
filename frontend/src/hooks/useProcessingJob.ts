/**
 * Hook for managing processing job state with SSE streaming
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type {
  ProcessingEvent,
  ProcessingJobState,
  StepName,
  InsightState,
  StepState,
} from '../types/streaming';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const STEP_ORDER: StepName[] = ['analyzing', 'planning', 'writing', 'validating', 'polishing'];

function initializeSteps(): StepState[] {
  return STEP_ORDER.map(name => ({
    name,
    progress: 0,
    status: 'pending' as const,
  }));
}

export function useProcessingJob(jobId: string | null) {
  const [state, setState] = useState<ProcessingJobState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastEventTsRef = useRef<number>(Date.now());
  const rafIdRef = useRef<number | null>(null);

  // Initialize state when jobId changes
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

  // Handle incoming events
  const handleEvent = useCallback((event: ProcessingEvent) => {
    lastEventTsRef.current = Date.now();

    setState(prev => {
      if (!prev) return prev;

      const newState = { ...prev };

      switch (event.type) {
        case 'job_status':
          newState.status = event.payload.status;
          break;

        case 'step_progress': {
          const { step, pct, eta_sec } = event.payload;
          newState.currentStep = step;
          
          // Update steps array
          newState.steps = prev.steps.map(s => {
            if (s.name === step) {
              return {
                ...s,
                progress: pct,
                eta_sec,
                status: pct === 100 ? 'completed' : 'in_progress',
              };
            }
            // Mark previous steps as completed
            const stepIndex = STEP_ORDER.indexOf(s.name);
            const currentIndex = STEP_ORDER.indexOf(step);
            if (stepIndex < currentIndex) {
              return { ...s, progress: 100, status: 'completed' };
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
          
          // Prepend new insights (most recent first)
          newState.insights = [insight, ...prev.insights];
          break;
        }

        case 'metric_update': {
          const { key, value, unit } = event.payload;
          newState.metrics = {
            ...prev.metrics,
            [key]: { key, value, unit },
          };
          
          // Special handling for application_id
          if (key === 'application_id') {
            newState.applicationId = value;
          }
          break;
        }

        case 'validation_update': {
          const validation = event.payload;
          const existingIndex = prev.validations.findIndex(
            v => v.rule_id === validation.rule_id
          );
          
          if (existingIndex >= 0) {
            newState.validations = [...prev.validations];
            newState.validations[existingIndex] = validation;
          } else {
            newState.validations = [...prev.validations, validation];
          }
          break;
        }

        case 'error':
          newState.connection = {
            ...prev.connection,
            error: event.payload.message,
          };
          break;

        case 'heartbeat':
          // Update connection lag
          newState.connection = {
            ...prev.connection,
            lagMs: Date.now() - event.ts,
            lastEventTs: event.ts,
          };
          break;

        case 'done':
          newState.status = 'completed';
          break;
      }

      return newState;
    });
  }, []);

  // Connect to SSE stream
  useEffect(() => {
    if (!jobId) return;

    const streamUrl = `${API_BASE_URL}/api/jobs/${jobId}/stream`;
    console.log('🔌 Connecting to SSE stream:', streamUrl);

    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('✅ SSE connection opened');
      setState(prev => prev ? {
        ...prev,
        connection: { ...prev.connection, connected: true, error: undefined },
      } : prev);
    };

    eventSource.onmessage = (e) => {
      try {
        const event: ProcessingEvent = JSON.parse(e.data);
        handleEvent(event);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('❌ SSE connection error:', err);
      setState(prev => prev ? {
        ...prev,
        connection: { ...prev.connection, connected: false, error: 'Connection lost' },
      } : prev);
      
      // EventSource will auto-reconnect
    };

    // Cleanup
    return () => {
      console.log('🔌 Closing SSE connection');
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [jobId, handleEvent]);

  // Monitor connection health
  useEffect(() => {
    if (!jobId || !state) return;

    const checkHealth = () => {
      const now = Date.now();
      const timeSinceLastEvent = now - lastEventTsRef.current;
      
      // If no event for 30s, mark as potentially stale
      if (timeSinceLastEvent > 30000) {
        setState(prev => prev ? {
          ...prev,
          connection: { ...prev.connection, error: 'Connection may be stale' },
        } : prev);
      }
      
      rafIdRef.current = requestAnimationFrame(checkHealth);
    };

    rafIdRef.current = requestAnimationFrame(checkHealth);

    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [jobId, state]);

  return {
    state,
    error,
    isConnected: state?.connection.connected ?? false,
    isComplete: state?.status === 'completed',
    isFailed: state?.status === 'failed',
  };
}
