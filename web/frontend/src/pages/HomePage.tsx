import { useState, useEffect, useRef } from 'react';
import { usePipeline } from '../hooks/usePipeline';
import { useDiscovery } from '../hooks/useDiscovery';
import { usePipelineBatch, type BatchConference } from '../hooks/usePipelineBatch';
import PipelineStepper from '../components/PipelineStepper';
import ConferenceCard, { ValidationResults } from '../components/ConferenceCard';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Play, X, ChevronDown, ChevronRight, CheckCircle2, Circle, Loader2, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Conference } from '../types/conference';
import type { PipelineStep, ValidationResult } from '../types/pipeline';

// ── Pipeline step constants ────────────────────────────────────

const PIPELINE_STEPS = [
  'scrape_homepage', 'extract_homepage', 'discover_links', 'probe_paths',
  'merge_links', 'scrape_sub_pages', 'extract_sub_pages', 'assemble_conference',
];

const STEP_LABELS: Record<string, string> = {
  scrape_homepage: 'Scraping homepage...',
  extract_homepage: 'Extracting homepage...',
  discover_links: 'Discovering links...',
  probe_paths: 'Probing paths...',
  merge_links: 'Merging links...',
  scrape_sub_pages: 'Scraping sub-pages...',
  extract_sub_pages: 'Extracting sub-pages...',
  assemble_conference: 'Assembling conference...',
};

// ── Shared sub-components ──────────────────────────────────────

function StepIndicator({ steps, step }: { steps: PipelineStep[]; step: string }) {
  const stepData = steps.find(s => s.step === step);
  if (!stepData) return <Circle className="size-3.5 text-muted-foreground/40" />;
  if (stepData.status === 'complete') return <CheckCircle2 className="size-3.5 text-green-500" />;
  if (stepData.status === 'error') return <X className="size-3.5 text-destructive" />;
  return <Loader2 className="size-3.5 text-primary animate-spin" />;
}

function SpeakerSection({ conference }: { conference: Conference }) {
  const [expanded, setExpanded] = useState(false);
  const speakers = conference.speakers ?? [];

  if (speakers.length === 0) {
    return (
      <div className="text-sm">
        <span className="text-muted-foreground">Speakers: </span>
        <span className="text-muted-foreground italic">Not confirmed for this edition</span>
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-1.5 text-left group"
      >
        <span className="text-sm">
          <span className="text-muted-foreground">Speakers: </span>
          <span>{conference.total_speakers} confirmed</span>
          {!expanded && speakers.length > 0 && (
            <span className="text-muted-foreground">
              {' — '}{speakers.slice(0, 3).map((s: any) => s.name).join(', ')}
              {speakers.length > 3 && `, and ${speakers.length - 3} more`}
            </span>
          )}
        </span>
        <ChevronDown className={cn('size-4 shrink-0 text-muted-foreground transition-transform', expanded && 'rotate-180')} />
      </button>

      {expanded && (
        <div className="mt-2 max-h-72 overflow-y-auto rounded-lg border bg-muted/20">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-muted/80 backdrop-blur">
              <tr className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2 hidden sm:table-cell">Title / Affiliation</th>
                <th className="px-3 py-2 w-20">Origin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {speakers.map((speaker: any, idx: number) => (
                <tr key={idx} className="hover:bg-muted/40">
                  <td className="px-3 py-2 font-medium text-foreground whitespace-nowrap">{speaker.name}</td>
                  <td className="px-3 py-2 text-muted-foreground hidden sm:table-cell">
                    {[speaker.title, speaker.affiliation].filter(Boolean).join(', ') || '—'}
                  </td>
                  <td className="px-3 py-2">
                    {speaker.is_usa === true && <Badge variant="outline" className="text-[10px] px-1.5 py-0">US</Badge>}
                    {speaker.is_usa === false && (
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0">{speaker.country || 'Non-US'}</Badge>
                    )}
                    {speaker.is_usa === null && speaker.country && (
                      <span className="text-xs text-muted-foreground">{speaker.country}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StepProgressBar({ steps, showLabel = false }: { steps: PipelineStep[]; showLabel?: boolean }) {
  const completedCount = steps.filter(s => s.status === 'complete').length;
  const totalSteps = PIPELINE_STEPS.length;

  return (
    <div className="flex items-center gap-1">
      {PIPELINE_STEPS.map((step) => (
        <div key={step} title={step} className="flex items-center">
          <StepIndicator steps={steps} step={step} />
        </div>
      ))}
      {showLabel && (
        <span className="ml-2 text-xs text-muted-foreground">
          Step {completedCount + 1}/{totalSteps}
        </span>
      )}
    </div>
  );
}

// ── Animation: subtle celebratory pulse on fresh completion ────

function useCompletionAnimation(conferences: Map<string, BatchConference>) {
  const [justCompleted, setJustCompleted] = useState<Set<string>>(new Set());
  const prevDone = useRef<Set<string>>(new Set());

  useEffect(() => {
    const nowDone = new Set<string>();
    for (const [url, c] of conferences) {
      if (c.status === 'done' && c.conference) {
        nowDone.add(url);
      }
    }
    const newlyDone = new Set<string>();
    for (const url of nowDone) {
      if (!prevDone.current.has(url)) {
        newlyDone.add(url);
      }
    }
    if (newlyDone.size > 0) {
      setJustCompleted(newlyDone);
      const timer = setTimeout(() => setJustCompleted(new Set()), 1500);
      prevDone.current = nowDone;
      return () => clearTimeout(timer);
    }
    prevDone.current = nowDone;
  }, [conferences]);

  return justCompleted;
}

// ── Single result card (expandable accordion) ──────────────────

function ConferenceResultCard({
  result, expandedUrl, onExplore, onCancel, onToggleExpand, pipelineState, animate,
}: {
  result: { url: string; title: string };
  expandedUrl: string | null;
  onExplore: () => void;
  onCancel: () => void;
  onToggleExpand: () => void;
  pipelineState: { steps: PipelineStep[]; conference: Conference | null; isRunning: boolean; error: string | null; validation: ValidationResult | null };
  animate?: boolean;
}) {
  const isExpanded = expandedUrl === result.url;
  const { steps, conference, isRunning, error, validation } = pipelineState;

  const completedSteps = steps.filter(s => s.status === 'complete').length;
  const currentStep = steps.find(s => s.status === 'start');
  const currentStepLabel = currentStep ? STEP_LABELS[currentStep.step] || currentStep.step : null;
  const isDone = conference !== null && !isRunning;

  return (
    <div className={cn(
      'border border-border rounded-lg overflow-hidden',
      animate && 'animate-conference-glow',
    )}>
      <div className="flex items-center gap-2 p-3 hover:bg-muted/50 transition-colors">
        <button
          onClick={onToggleExpand}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          {isExpanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn(
              'font-medium truncate',
              animate && 'text-green-600 dark:text-green-400',
            )}>
              {result.title || result.url}
            </span>
            {isDone && <CheckCircle2 className="size-4 text-green-500 shrink-0" />}
          </div>
          <div className="text-xs text-muted-foreground truncate">{result.url}</div>
        </div>
        {isRunning ? (
          <Button variant="ghost" size="icon-xs" onClick={onCancel} title="Cancel">
            <X className="size-3.5" />
          </Button>
        ) : (
          <Button variant="ghost" size="icon-xs" onClick={onExplore} title="Explore">
            <Play className="size-3.5" />
          </Button>
        )}
      </div>
      {isExpanded && (
        <div className="border-t border-border p-3 bg-muted/20">
          {isRunning && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">
                  {currentStepLabel || 'Pipeline running...'}
                </div>
                {steps.length > 0 && (
                  <div className="text-xs text-muted-foreground">
                    {completedSteps}/{PIPELINE_STEPS.length} steps
                  </div>
                )}
              </div>
              <StepProgressBar steps={steps} />
            </div>
          )}
          {error && <div className="text-xs text-destructive">Error: {error}</div>}
          {conference && (
            <div className="space-y-4 border-t border-border pt-3 mt-3">
              <div className="flex flex-wrap items-center gap-2">
                <div className={cn('text-lg font-bold', isDone && animate && 'animate-conference-name')}>{conference.conference_name}</div>
                {conference.conference_acronym && (
                  <Badge variant="secondary" className="text-xs shrink-0">{conference.conference_acronym}</Badge>
                )}
                {conference.conference_format && (
                  <Badge variant="outline" className="text-xs shrink-0">{conference.conference_format}</Badge>
                )}
              </div>
              {conference.date_start && conference.date_end && (
                <div className="text-sm"><span className="text-muted-foreground">Dates: </span><span>{conference.date_start} – {conference.date_end}</span></div>
              )}
              {conference.industry && (
                <div className="text-sm"><span className="text-muted-foreground">Industry: </span><span>{conference.industry}</span></div>
              )}
              {conference.organizer && (
                <div className="text-sm"><span className="text-muted-foreground">Organizer: </span><span>{conference.organizer}</span></div>
              )}
              {conference.submission_deadline && (
                <div className="text-sm"><span className="text-muted-foreground">Submission: </span><span>{conference.submission_deadline}</span></div>
              )}
              {(conference.venue_name || conference.venue_address || conference.venue_city || conference.venue_country) && (
                <div className="text-sm"><span className="text-muted-foreground">Venue: </span><span>{[conference.venue_name, conference.venue_address, conference.venue_city, conference.venue_country].filter(Boolean).join(', ')}</span></div>
              )}
              <SpeakerSection conference={conference} />
              {conference.total_speakers > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-2 py-2">
                    <span className="text-lg font-bold tabular-nums leading-none text-foreground">{conference.total_speakers}</span>
                    <span className="text-[10px] text-muted-foreground">Total</span>
                  </div>
                  <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-2 py-2">
                    <span className="text-lg font-bold tabular-nums leading-none text-foreground">{conference.non_local_count}</span>
                    <span className="text-[10px] text-muted-foreground">Non-local</span>
                  </div>
                  <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-2 py-2">
                    <span className="text-lg font-bold tabular-nums leading-none text-foreground">{conference.non_usa_count}</span>
                    <span className="text-[10px] text-muted-foreground">Non-USA</span>
                  </div>
                </div>
              )}
              {conference.sector_tags?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {conference.sector_tags.map((tag: string, i: number) => (
                    <span key={i} className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{tag}</span>
                  ))}
                </div>
              )}
              {(conference.fee_range_usd || conference.early_bird_deadline) && (
                <div className="text-sm space-y-0.5">
                  {conference.fee_range_usd && <div><span className="text-muted-foreground">Fee: </span><span>{conference.fee_range_usd}</span></div>}
                  {conference.early_bird_deadline && <div><span className="text-muted-foreground">Early bird: </span><span>{conference.early_bird_deadline}</span></div>}
                </div>
              )}
              <div className="text-sm">
                <span className="text-muted-foreground">Covers accommodation: </span>
                <span className={conference.covers_accommodation ? 'text-green-600 dark:text-green-400 font-medium' : 'text-muted-foreground'}>
                  {conference.covers_accommodation ? 'Yes' : 'No'}
                </span>
              </div>
              {conference.website_url && (
                <a href={conference.website_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline break-all">{conference.website_url}</a>
              )}
              {validation && (
                <ValidationResults validation={validation} />
              )}
            </div>
          )}
          {!isRunning && !error && !conference && (
            <div className="text-xs text-muted-foreground">Click Explore to run the pipeline</div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Batch status card ──────────────────────────────────────────

function BatchStatusCard({ batch, onRetry, showRetry, animate }: {
  batch: BatchConference;
  onRetry?: () => void;
  showRetry?: boolean;
  animate?: boolean;
}) {
  const currentStep = batch.steps.find(s => s.status === 'start');
  const currentStepLabel = currentStep ? STEP_LABELS[currentStep.step] || currentStep.step : null;

  return (
    <div className={cn(
      'border border-border rounded-lg p-3 space-y-2',
      animate && 'animate-conference-glow',
    )}>
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className={cn('font-medium text-sm truncate', animate && !batch.conference && 'text-green-600 dark:text-green-400', animate && batch.conference && 'animate-conference-name')}>
              {batch.title || batch.url}
            </div>
            {batch.status === 'done' && batch.conference && <CheckCircle2 className="size-4 text-green-500 shrink-0" />}
          </div>
          <div className="text-xs text-muted-foreground truncate">{batch.url}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {batch.status === 'running' && currentStepLabel && (
            <span className="text-xs text-muted-foreground">{currentStepLabel}</span>
          )}
          <Badge variant={
            batch.status === 'done' ? 'default' :
            batch.status === 'error' ? 'destructive' :
            batch.status === 'running' ? 'secondary' : 'outline'
          }>
            {batch.status === 'pending' && 'Pending'}
            {batch.status === 'running' && 'Running'}
            {batch.status === 'done' && 'Done'}
            {batch.status === 'error' && 'Error'}
          </Badge>
        </div>
      </div>
      {(batch.status === 'running' || batch.steps.length > 0) && (
        <div className="space-y-1"><StepProgressBar steps={batch.steps} showLabel /></div>
      )}
      {batch.status === 'running' && batch.elapsed > 0 && (
        <div className="text-xs text-muted-foreground">{batch.elapsed.toFixed(1)}s elapsed</div>
      )}
      {batch.status === 'error' && batch.error && (
        <div className="text-xs text-destructive">Failed: {batch.error}</div>
      )}
      {showRetry && batch.status === 'error' && onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="w-full mt-1">
          <RotateCcw className="size-3.5 mr-1" /> Retry
        </Button>
      )}
      {batch.conference && (
        <div className="space-y-3 bg-muted/30 rounded-lg p-4 mt-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className={cn('text-base font-bold leading-tight', animate && 'animate-conference-name')}>
              {batch.conference.conference_name}
            </div>
            {batch.conference.conference_acronym && (
              <Badge variant="secondary" className="text-xs shrink-0">{batch.conference.conference_acronym}</Badge>
            )}
            {batch.conference.conference_format && (
              <Badge variant="outline" className="text-xs shrink-0">{batch.conference.conference_format}</Badge>
            )}
          </div>
          {(batch.conference.date_start || batch.conference.date_end) && (
            <div className="text-sm"><span className="text-muted-foreground">Dates: </span><span>{batch.conference.date_start || 'TBA'} – {batch.conference.date_end || 'TBA'}</span></div>
          )}
          {batch.conference.industry && (
            <div className="text-sm"><span className="text-muted-foreground">Industry: </span><span>{batch.conference.industry}</span></div>
          )}
          {batch.conference.organizer && (
            <div className="text-sm"><span className="text-muted-foreground">Organizer: </span><span>{batch.conference.organizer}</span></div>
          )}
          {(batch.conference.venue_name || batch.conference.venue_address || batch.conference.venue_city || batch.conference.venue_country) && (
            <div className="text-sm"><span className="text-muted-foreground">Venue: </span><span>{[batch.conference.venue_name, batch.conference.venue_address, batch.conference.venue_city, batch.conference.venue_country].filter(Boolean).join(', ')}</span></div>
          )}
          <SpeakerSection conference={batch.conference} />
          {batch.conference.total_speakers > 0 && (
            <div className="grid grid-cols-3 gap-2">
              <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-2 py-2">
                <span className="text-lg font-bold tabular-nums leading-none text-foreground">{batch.conference.total_speakers}</span>
                <span className="text-[10px] text-muted-foreground">Total</span>
              </div>
              <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-2 py-2">
                <span className="text-lg font-bold tabular-nums leading-none text-foreground">{batch.conference.non_local_count}</span>
                <span className="text-[10px] text-muted-foreground">Non-local</span>
              </div>
              <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-2 py-2">
                <span className="text-lg font-bold tabular-nums leading-none text-foreground">{batch.conference.non_usa_count}</span>
                <span className="text-[10px] text-muted-foreground">Non-USA</span>
              </div>
            </div>
          )}
          {batch.conference.sector_tags?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {batch.conference.sector_tags.map((tag: string, i: number) => (
                <span key={i} className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{tag}</span>
              ))}
            </div>
          )}
          {batch.conference.submission_deadline && (
            <div className="text-sm"><span className="text-muted-foreground">Submission deadline: </span><span>{batch.conference.submission_deadline}</span></div>
          )}
          {(batch.conference.fee_range_usd || batch.conference.early_bird_deadline) && (
            <div className="text-sm space-y-0.5">
              {batch.conference.fee_range_usd && <div><span className="text-muted-foreground">Fee: </span><span>{batch.conference.fee_range_usd}</span></div>}
              {batch.conference.early_bird_deadline && <div><span className="text-muted-foreground">Early bird: </span><span>{batch.conference.early_bird_deadline}</span></div>}
            </div>
          )}
          <div className="text-sm">
            <span className="text-muted-foreground">Covers accommodation: </span>
            <span className={batch.conference.covers_accommodation ? 'text-green-600 dark:text-green-400 font-medium' : 'text-muted-foreground'}>
              {batch.conference.covers_accommodation ? 'Yes' : 'No'}
            </span>
          </div>
          {batch.conference.website_url && (
            <a href={batch.conference.website_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline break-all">{batch.conference.website_url}</a>
          )}
          {batch.validation && (
            <ValidationResults validation={batch.validation} />
          )}
        </div>
      )}
      {batch.status === 'done' && !batch.conference && (
        <div className="text-xs text-muted-foreground">No conference data extracted</div>
      )}
    </div>
  );
}

// ── Main HomePage ──────────────────────────────────────────────

export default function HomePage() {
  // ── URL pipeline state ──
  const [url, setUrl] = useState('');
  const [urlError, setUrlError] = useState('');
  const { steps, conference, validation, isRunning, error, startPipeline, cancelPipeline } = usePipeline();

  // ── Discovery state ──
  const [topic, setTopic] = useState('medical');
  const [monthsAhead, setMonthsAhead] = useState(3);
  const [numResults, setNumResults] = useState(5);
  const { results, isRunning: isDiscoveryRunning, isSearching, foundCount, error: discoveryError, elapsed, startDiscovery, clearResults } = useDiscovery();
  const { conferences, isRunning: isBatchRunning, totalElapsed, startBatch, cancelBatch, clearResults: clearBatch } = usePipelineBatch();

  // ── UI state ──
  const [expandedUrl, setExpandedUrl] = useState<string | null>(null);
  const [singleExploreUrl, setSingleExploreUrl] = useState<string | null>(null);
  const resultsEndRef = useRef<HTMLDivElement | null>(null);
  const hasRunRef = useRef(false);
  const justCompleted = useCompletionAnimation(conferences);

  // ── Auto-run discovery on first visit ──
  useEffect(() => {
    if (!hasRunRef.current) {
      hasRunRef.current = true;
      const stored = sessionStorage.getItem('discovery_results');
      if (!stored || JSON.parse(stored).length === 0) {
        startDiscovery(topic, monthsAhead, numResults);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Auto-scroll ──
  useEffect(() => {
    if (results.length > 0 && resultsEndRef.current) {
      resultsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [results.length]);

  // ── URL input handlers ──
  const handleUrlRun = () => {
    if (!url.trim()) return;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setUrlError('Please enter a valid URL starting with http:// or https://');
      return;
    }
    setUrlError('');
    startPipeline(url.trim());
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    if (urlError) setUrlError('');
  };

  // ── Discovery handlers ──
  const handleDiscoveryRun = () => startDiscovery(topic, monthsAhead, numResults);
  const handleExploreSingle = (u: string) => { setSingleExploreUrl(u); setExpandedUrl(u); startPipeline(u); };
  const handleCancelSingle = () => { cancelPipeline(); setSingleExploreUrl(null); setExpandedUrl(null); };
  const handleExploreAll = () => { clearBatch(); startBatch(results.map(r => ({ url: r.url, title: r.title }))); };
  const handleRetryFailed = () => {
    const failedUrls = Array.from(conferences.values()).filter(c => c.status === 'error').map(c => ({ url: c.url, title: c.title }));
    if (failedUrls.length > 0) startBatch(failedUrls);
  };
  const handleToggleExpand = (u: string) => setExpandedUrl(prev => prev === u ? null : u);
  const handleClearAll = () => { clearResults(); clearBatch(); };

  // ── Computed flags ──
  const isAnyRunning = isRunning || isDiscoveryRunning || isBatchRunning;
  const showStepper = isRunning || steps.length > 0;
  const showResult = conference !== null || (steps.length > 0 && !isRunning && !error);
  const showError = error && !isRunning;
  const hasDiscoveryResults = results.length > 0;
  const hasBatchResults = conferences.size > 0;
  const batchSucceeded = Array.from(conferences.values()).filter(c => c.status === 'done' && c.conference).length;
  const batchFailed = Array.from(conferences.values()).filter(c => c.status === 'error').length;

  return (
    <div data-testid="home-page" className="home-page space-y-6">
      {/* ── URL Input Section ── */}
      <div className="url-input-section rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold mb-2">Conference URL</h2>
        <div className="url-input-row flex gap-2">
          <input
            type="url"
            value={url}
            onChange={handleUrlChange}
            placeholder="https://example-conference.org/"
            disabled={isRunning}
            data-testid="url-input"
            className="url-input flex-1"
          />
          {isRunning ? (
            <button onClick={cancelPipeline} data-testid="cancel-button" className="btn-cancel shrink-0">Cancel</button>
          ) : (
            <button onClick={handleUrlRun} disabled={!url.trim()} data-testid="run-button" className="btn-run shrink-0">Run Pipeline</button>
          )}
        </div>
        {urlError && <p className="url-validation-error text-sm text-destructive mt-1" data-testid="url-validation-error">{urlError}</p>}

        {/* Divider */}
        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
          <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">Or search for conferences</span></div>
        </div>

        {/* ── Discovery Search Form ── */}
        <div className="discovery-form space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Topic</label>
            <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. medical, engineering, AI" disabled={isAnyRunning} data-testid="discovery-topic-input" className="url-input w-full" />
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">Months ahead: {monthsAhead}</label>
              <input type="range" min={1} max={12} value={monthsAhead} onChange={(e) => setMonthsAhead(Number(e.target.value))} disabled={isAnyRunning} data-testid="discovery-months-input" className="w-full" />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">Results: {numResults}</label>
              <input type="range" min={1} max={20} value={numResults} onChange={(e) => setNumResults(Number(e.target.value))} disabled={isAnyRunning} data-testid="discovery-results-input" className="w-full" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleDiscoveryRun} disabled={isAnyRunning || !topic.trim()} data-testid="discovery-run-button" className="btn-run">
              {isDiscoveryRunning ? 'Searching...' : 'Search'}
            </button>
            {hasDiscoveryResults && (
              <button onClick={handleClearAll} disabled={isAnyRunning} className="btn-cancel">Clear</button>
            )}
          </div>
        </div>
      </div>

      {/* ── Discovery streaming status ── */}
      {isSearching && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground" data-testid="discovery-loading">
          <Loader2 className="size-4 animate-spin shrink-0" />
          <span>Searching... <span className="font-medium text-foreground animate-pulse">{foundCount}</span> found so far ({elapsed.toFixed(1)}s)</span>
        </div>
      )}
      {!isSearching && isDiscoveryRunning && (
        <div className="text-sm text-muted-foreground" data-testid="discovery-loading">Processing results... ({elapsed.toFixed(1)}s)</div>
      )}
      {discoveryError && (
        <div className="error-banner text-sm text-destructive bg-destructive/10 p-3 rounded-lg" data-testid="discovery-error">{discoveryError}</div>
      )}

      {/* ── Pipeline stepper + result (direct URL) ── */}
      {showStepper && (
        <div className="stepper-section rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wider">Pipeline Progress</h3>
          <PipelineStepper steps={steps} />
        </div>
      )}
      {showError && (
        <div className="error-section rounded-xl border border-destructive/30 bg-destructive/5 p-5" data-testid="pipeline-error">
          <p className="error-message text-sm font-medium text-destructive">{error}</p>
          <p className="error-hint text-xs text-muted-foreground mt-1">Try a different URL or check that services are running.</p>
        </div>
      )}
      {showResult && (
        <div className="result-section">
          <ConferenceCard conference={conference} validation={validation} isLoading={false} />
        </div>
      )}

      {/* ── Discovery results list ── */}
      {!isDiscoveryRunning && hasDiscoveryResults && !hasBatchResults && (
        <div data-testid="discovery-results" className="rounded-xl border bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              Found {results.length} conference{results.length !== 1 ? 's' : ''} in {elapsed.toFixed(1)}s
            </p>
            <div className="flex gap-2">
              <Button variant="default" size="sm" onClick={handleExploreAll} disabled={isAnyRunning}>
                <Play className="size-4 mr-1" /> Explore ALL
              </Button>
            </div>
          </div>
          <ul className="space-y-2">
            {results.map((r, idx) => (
              <li key={r.url + idx}>
                <ConferenceResultCard
                   result={r}
                   expandedUrl={singleExploreUrl === r.url ? expandedUrl : null}
                  onExplore={() => handleExploreSingle(r.url)}
                  onCancel={handleCancelSingle}
                  onToggleExpand={() => handleToggleExpand(r.url)}
                  pipelineState={singleExploreUrl === r.url
                    ? { steps, conference, isRunning, error, validation }
                    : { steps: [], conference: null, isRunning: false, error: null, validation: null }
                  }
                />
              </li>
            ))}
            <div ref={resultsEndRef} />
          </ul>
        </div>
      )}

      {/* ── Batch pipeline status ── */}
      {hasBatchResults && (
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">
                {isBatchRunning ? 'Exploring conferences...' : 'Batch Complete'}
              </span>
              {isBatchRunning ? (
                <span className="text-sm text-muted-foreground">({totalElapsed.toFixed(1)}s)</span>
              ) : (
                <span className="text-sm text-muted-foreground">
                  ({batchSucceeded} succeeded{batchFailed > 0 && <span className="text-destructive">, {batchFailed} failed</span>} out of {conferences.size})
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {!isBatchRunning && batchFailed > 0 && (
                <Button variant="outline" size="sm" onClick={handleRetryFailed}><RotateCcw className="size-3.5 mr-1" /> Retry ({batchFailed})</Button>
              )}
              {isBatchRunning ? (
                <Button variant="ghost" size="sm" onClick={cancelBatch}><X className="size-4 mr-1" /> Cancel</Button>
              ) : (
                <Button variant="ghost" size="sm" onClick={handleClearAll}>Clear</Button>
              )}
            </div>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {Array.from(conferences.values()).map(conf => (
              <BatchStatusCard key={conf.url} batch={conf} showRetry={!isBatchRunning && batchFailed > 0} onRetry={handleRetryFailed} animate={justCompleted.has(conf.url)} />
            ))}
          </div>
        </div>
      )}

      {/* ── Empty state ── */}
      {!isDiscoveryRunning && results.length === 0 && !discoveryError && hasRunRef.current && !showStepper && !hasBatchResults && (
        <div className="text-sm text-muted-foreground text-center py-12" data-testid="discovery-empty">
          No conferences found. Try broadening the topic or increasing months ahead.
        </div>
      )}
    </div>
  );
}
