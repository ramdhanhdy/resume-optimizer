
export enum Screen {
  Input,
  Processing,
  Reveal,
}

export interface Insight {
  id: string | number;
  text: string;
  category: string;
}

export interface Validation {
  level: 'warning';
  message: string;
  suggestion: string;
}

export interface ResumeChange {
  id: number;
  original: string;
  optimized: string;
  reason: string;
  validation?: Validation;
}
