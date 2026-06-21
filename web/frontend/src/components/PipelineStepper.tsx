import type { PipelineStep } from '../types/pipeline';
import type { StepStatus } from '../types/pipeline';
import { cn } from '@/lib/utils';

// ── Props ──────────────────────────────────────────────────────────

interface PipelineStepperProps {
  steps: PipelineStep[];
}

// ── Default steps (shown when steps array is empty or partial) ─────

const DEFAULT_STEPS = [
  { step: 'discover_conferences', label: 'Discover conferences', index: 1 },
  { step: 'scrape_homepage', label: 'Scrape homepage', index: 2 },
  { step: 'extract_homepage', label: 'Extract homepage', index: 3 },
  { step: 'discover_links', label: 'Discover links', index: 4 },
  { step: 'probe_paths', label: 'Probe paths', index: 5 },
  { step: 'merge_links', label: 'Merge links', index: 6 },
  { step: 'scrape_sub_pages', label: 'Scrape sub-pages', index: 7 },
  { step: 'extract_sub_pages', label: 'Extract sub-pages', index: 8 },
  { step: 'assemble_conference', label: 'Assemble Conference', index: 9 },
  { step: 'validate_conference', label: 'Validate', index: 10 },
] as const;

// ── Helpers ────────────────────────────────────────────────────────

type StepDisplay = {
  status: StepStatus | 'pending';
  elapsed?: number;
  error?: string | null;
};

function getStepStatus(step: string, steps: PipelineStep[]): StepDisplay {
  const match = steps.find((s) => s.step === step);
  if (!match) return { status: 'pending' };
  return { status: match.status, elapsed: match.elapsed, error: match.error };
}

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s.toFixed(0)}s`;
}

// ── Status icon component ──────────────────────────────────────────

function StatusDot({ status }: { status: StepStatus | 'pending' }) {
  switch (status) {
    case 'complete':
      return (
        <svg
          viewBox="0 0 16 16"
          className="size-4 text-green-500"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="3 8 7 12 13 4" />
        </svg>
      );
    case 'error':
      return (
        <svg
          viewBox="0 0 16 16"
          className="size-4 text-destructive"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="3" y1="3" x2="13" y2="13" />
          <line x1="13" y1="3" x2="3" y2="13" />
        </svg>
      );
    case 'start':
      return (
        <span className="relative flex size-4 items-center justify-center">
          <span className="absolute inset-0 rounded-full bg-blue-500/35 animate-pipeline-pulse" />
          <span className="size-2 rounded-full bg-blue-500" />
        </span>
      );
    default:
      return <span className="size-2 rounded-full bg-muted-foreground/40" />;
  }
}

// ── Main component ─────────────────────────────────────────────────

export default function PipelineStepper({ steps }: PipelineStepperProps) {
  return (
    <div data-testid="pipeline-stepper" className="w-full">
      {/* Keyframe animations */}
      <style>{`
        @keyframes pipeline-pulse-ring {
          0%   { transform: scale(1);   opacity: 0.6; }
          50%  { transform: scale(2.2);  opacity: 0;   }
          100% { transform: scale(1);   opacity: 0.6; }
        }
        .animate-pipeline-pulse {
          animation: pipeline-pulse-ring 1.8s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>

      <div className="relative">
        {DEFAULT_STEPS.map((defaultStep, idx) => {
          const { status, elapsed, error } = getStepStatus(defaultStep.step, steps);
          const isLast = idx === DEFAULT_STEPS.length - 1;

          return (
            <div key={defaultStep.step} data-testid={`step-${defaultStep.step}`}>
              <div className="flex items-start gap-3 py-1.5">
                {/* ── Step number circle + status ── */}
                <div className="relative flex flex-col items-center">
                  <div
                    className={cn(
                      'flex size-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors duration-200',
                      status === 'pending' &&
                        'border-muted-foreground/30 text-muted-foreground/60',
                      status === 'start' &&
                        'border-blue-500 text-blue-500',
                      status === 'complete' &&
                        'border-green-500 text-green-500',
                      status === 'error' &&
                        'border-destructive text-destructive',
                    )}
                  >
                    {defaultStep.index}
                  </div>

                  {/* Connecting line */}
                  {!isLast && (
                    <div
                      className={cn(
                        'mt-1 w-0.5 grow rounded-full transition-colors duration-300',
                        status === 'complete' ? 'bg-green-500/40' : 'bg-border',
                      )}
                      style={{ minHeight: '1.5rem' }}
                    />
                  )}
                </div>

                {/* ── Label + metadata ── */}
                <div className="flex min-w-0 flex-1 items-center gap-2 pt-1.5">
                  <span
                    className={cn(
                      'truncate text-sm font-medium transition-colors duration-200',
                      status === 'pending' && 'text-muted-foreground/70',
                      status === 'start' && 'text-foreground',
                      status === 'complete' && 'text-foreground',
                      status === 'error' && 'text-foreground',
                    )}
                  >
                    {defaultStep.label}
                  </span>

                  <div className="ml-auto flex shrink-0 items-center gap-2">
                    {elapsed !== undefined && (
                      <span className="tabular-nums text-xs text-muted-foreground/70">
                        {formatElapsed(elapsed)}
                      </span>
                    )}
                    <StatusDot status={status} />
                  </div>
                </div>
              </div>

              {/* ── Error message ── */}
              {status === 'error' && error && (
                <div className="ml-11 pb-2">
                  <p className="text-xs leading-relaxed text-destructive">
                    {error}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
