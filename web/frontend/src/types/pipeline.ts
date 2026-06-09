import type {
  StepStartData,
  StepCompleteData,
  StepErrorData,
  PipelineCompleteData,
  DiscoveryCompleteData,
} from './pipeline';

/** SSE event data for discovery search */
export interface DiscoveryCompleteData {
  results: Array<{ url: string; title: string }>;
  total_elapsed: number;
  steps_completed: number;
  total_found: number;
  accepted: number;
}

export type DiscoveryEvent =
  | { event: 'step_complete'; data: StepCompleteData }
  | { event: 'pipeline_complete'; data: DiscoveryCompleteData }
  | { event: 'done'; data: Record<string, never> };
