/** A pipeline step with its progress status */
export interface PipelineStep {
  step: string;
  label: string;
  index: number;
  total: number;
  elapsed: number;
  status: 'start' | 'complete' | 'error';
  error: string | null;
}

/** Step start event data */
export interface StepStartData {
  url?: string;
  step: string;
  label: string;
  index: number;
  total: number;
  steps_total?: number;
  step_index?: number;
  elapsed: number;
}

/** Step complete event data */
export interface StepCompleteData {
  url?: string;
  step: string;
  label: string;
  index: number;
  total: number;
  steps_total?: number;
  step_index?: number;
  elapsed: number;
}

/** Step error event data */
export interface StepErrorData {
  url?: string;
  step: string;
  label: string;
  index: number;
  total: number;
  steps_total?: number;
  step_index?: number;
  elapsed: number;
  error: string;
}

/** Pipeline complete event data */
export interface PipelineCompleteData {
  conference: Record<string, unknown> | null;
  total_elapsed: number;
  steps_completed: number;
}

/** SSE event data for discovery search */
export interface DiscoveryCompleteData {
  results: Array<{ url: string; title: string }>;
  total_elapsed: number;
  steps_completed: number;
  total_found: number;
  accepted: number;
}

/** Batch started event data */
export interface BatchStartedData {
  total: number;
  urls: string[];
  elapsed: number;
}

/** Conference start event data */
export interface ConferenceStartData {
  url: string;
  index: number;
  total: number;
  elapsed: number;
}

/** Conference complete event data */
export interface ConferenceCompleteData {
  url: string;
  conference: Record<string, unknown> | null;
  total_elapsed: number;
  steps_completed: number;
  elapsed: number;
}

/** Conference error event data */
export interface ConferenceErrorData {
  url: string;
  error: string;
  elapsed: number;
}

/** Batch complete event data */
export interface BatchCompleteData {
  total: number;
  elapsed: number;
}

export type DiscoveryEvent =
  | { event: 'step_complete'; data: StepCompleteData }
  | { event: 'pipeline_complete'; data: DiscoveryCompleteData }
  | { event: 'done'; data: Record<string, never> };