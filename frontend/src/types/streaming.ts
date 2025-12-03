/**
 * Types for SSE streaming events from backend
 */

export type JobStatus = 'started' | 'running' | 'completed' | 'failed' | 'canceled';
export type StepName = 'analyzing' | 'planning' | 'writing' | 'validating' | 'polishing';
export type InsightImportance = 'low' | 'medium' | 'high';
export type ValidationStatus = 'pass' | 'warn' | 'fail';

export interface BaseEvent {
  type: string;
  ts: number;
  job_id: string;
}

export interface JobStatusEvent extends BaseEvent {
  type: 'job_status';
  payload: {
    status: JobStatus;
  };
}

export interface StepProgressEvent extends BaseEvent {
  type: 'step_progress';
  payload: {
    step: StepName;
    pct: number;
    eta_sec?: number;
  };
}

export interface InsightEvent extends BaseEvent {
  type: 'insight_emitted';
  payload: {
    id: string;
    category: string;
    importance: InsightImportance;
    message: string;
    step?: StepName;
  };
}

export interface MetricUpdateEvent extends BaseEvent {
  type: 'metric_update';
  payload: {
    key: string;
    value: number;
    unit?: string;
  };
}

export interface ValidationUpdateEvent extends BaseEvent {
  type: 'validation_update';
  payload: {
    rule_id: string;
    status: ValidationStatus;
    message?: string;
  };
}

export interface DiffChunkEvent extends BaseEvent {
  type: 'diff_chunk';
  payload: {
    section: string;
    summary: string;
    patch_id?: string;
  };
}

export interface ErrorEvent extends BaseEvent {
  type: 'error';
  payload: {
    code: string;
    message: string;
  };
}

export interface HeartbeatEvent extends BaseEvent {
  type: 'heartbeat';
  payload: Record<string, never>;
}

export interface DoneEvent extends BaseEvent {
  type: 'done';
  payload: Record<string, never>;
}

export type ProcessingEvent =
  | JobStatusEvent
  | StepProgressEvent
  | InsightEvent
  | MetricUpdateEvent
  | ValidationUpdateEvent
  | DiffChunkEvent
  | ErrorEvent
  | HeartbeatEvent
  | DoneEvent;

// State types
export interface StepState {
  name: StepName;
  progress: number;
  eta_sec?: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  startedAt?: number;  // Timestamp when step started (ms)
  completedAt?: number; // Timestamp when step completed (ms)
}

export interface InsightState {
  id: string;
  category: string;
  importance: InsightImportance;
  message: string;
  step?: StepName;
  ts: number;
  pinned?: boolean;
}

export interface MetricState {
  key: string;
  value: number;
  unit?: string;
}

export interface ValidationState {
  rule_id: string;
  status: ValidationStatus;
  message?: string;
}

export interface ConnectionState {
  connected: boolean;
  lagMs: number;
  lastEventTs: number;
  error?: string;
}

export interface ProcessingJobState {
  jobId: string;
  status: JobStatus;
  currentStep?: StepName;
  steps: StepState[];
  insights: InsightState[];
  metrics: Record<string, MetricState>;
  validations: ValidationState[];
  connection: ConnectionState;
  applicationId?: number;
}
