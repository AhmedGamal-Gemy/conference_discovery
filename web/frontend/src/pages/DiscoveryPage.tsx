import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useDiscovery } from '../hooks/useDiscovery';
import { usePipeline } from '../hooks/usePipeline';
import { usePipelineBatch, type BatchConference } from '../hooks/usePipelineBatch';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Play, X, ChevronDown, ChevronRight, CheckCircle2, Circle, XCircle, Loader2, RotateCcw, ChevronUp } from 'lucide-react';
import { cn } from '../lib/utils';
import type { Conference } from '../types/conference';
import type { PipelineStep } from '../types/pipeline';

const PIPELINE_STEPS = [
  'scrape_homepage',
  'extract_homepage',
  'discover_links',
  'probe_paths',
  'merge_links',
  'scrape_sub_pages',
  'extract_sub_pages',
  'assemble_conference',
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

function StepIndicator({ steps, step }: { steps: PipelineStep[]; step: string }) {
  const stepData = steps.find(s => s.step === step);
  if (!stepData) return <Circle className="size-3.5 text-muted-foreground/40" />;
  if (stepData.status === 'complete') return <CheckCircle2 className="size-3.5 text-green-500" />;
  if (stepData.status === 'error') return <XCircle className="size-3.5 text-destructive" />;
  return <Loader2 className="size-3.5 text-primary animate-spin" />;
}

function SpeakerSection({ conference }: { conference: Conference }) {
  const [expanded, setExpanded] = useState(false);
  const speakers = conference.speakers ?? [];

  if (speakers.length === 0) return null;

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
  const currentStep = steps.find(s => s.status === 'start' || s.status === 'complete' && steps.filter(st => st.status === 'complete').length - 1 === steps.indexOf(s));

  return (
    <div className="flex items-center gap-1">
      {PIPELINE_STEPS.map((step, idx) => (
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

function ConferenceResultCard({
  result,
  index,
  expandedUrl,
  onExplore,
  onCancel,
  onToggleExpand,
  pipelineState,
}: {
  result: { url: string; title: string };
  index: number;
  expandedUrl: string | null;
  onExplore: () => void;
  onCancel: () => void;
  onToggleExpand: () => void;
  pipelineState: { steps: PipelineStep[]; conference: Conference | null; isRunning: boolean; error: string | null };
}) {
  const isExpanded = expandedUrl === result.url;
  const { steps, conference, isRunning, error } = pipelineState;

  const completedSteps = steps.filter(s => s.status === 'complete').length;
  const currentStep = steps.find(s => s.status === 'start');
  const currentStepLabel = currentStep ? STEP_LABELS[currentStep.step] || currentStep.step : null;
  const isDone = conference !== null && !isRunning;

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 p-3 hover:bg-muted/50 transition-colors">
        <button
          onClick={onToggleExpand}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          {isExpanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
        </button>
        <button
          onClick={() => window.location.href = `/?url=${encodeURIComponent(result.url)}`}
          data-testid={`discovery-result-${index}`}
          className="flex-1 text-left min-w-0"
        >
          <div className="flex items-center gap-2">
            <span className="font-medium truncate">{result.title || result.url}</span>
            {isDone && (
              <CheckCircle2 className="size-4 text-green-500 shrink-0" />
            )}
          </div>
          <div className="text-xs text-muted-foreground truncate">{result.url}</div>
        </button>
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
          {error && (
            <div className="text-xs text-destructive">Error: {error}</div>
          )}
          {conference && (
            <div className="space-y-4 border-t border-border pt-3 mt-3">
              <div className="text-lg font-bold">{conference.conference_name}</div>
              {conference.date_start && conference.date_end && (
                <div className="text-sm">
                  <span className="text-muted-foreground">Dates: </span>
                  <span>{conference.date_start} – {conference.date_end}</span>
                </div>
              )}
              {(conference.venue_city || conference.venue_country) && (
                <div className="text-sm">
                  <span className="text-muted-foreground">Venue: </span>
                  <span>{[conference.venue_city, conference.venue_country].filter(Boolean).join(', ')}</span>
                </div>
              )}
              <SpeakerSection conference={conference} />

              {/* Stats row */}
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
                  {conference.fee_range_usd && (
                    <div><span className="text-muted-foreground">Fee: </span><span>{conference.fee_range_usd}</span></div>
                  )}
                  {conference.early_bird_deadline && (
                    <div><span className="text-muted-foreground">Early bird: </span><span>{conference.early_bird_deadline}</span></div>
                  )}
                </div>
              )}
              {conference.website_url && (
                <a href={conference.website_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline break-all">
                  {conference.website_url}
                </a>
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

function BatchStatusCard({
  batch,
  onRetry,
  showRetry,
}: {
  batch: BatchConference;
  onRetry?: () => void;
  showRetry?: boolean;
}) {
  const completedSteps = batch.steps.filter(s => s.status === 'complete').length;
  const currentStep = batch.steps.find(s => s.status === 'start');
  const currentStepLabel = currentStep ? STEP_LABELS[currentStep.step] || currentStep.step : null;

  return (
    <div className="border border-border rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="font-medium text-sm truncate">{batch.title || batch.url}</div>
            {batch.status === 'done' && batch.conference && (
              <CheckCircle2 className="size-4 text-green-500 shrink-0" />
            )}
          </div>
          <div className="text-xs text-muted-foreground truncate">{batch.url}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {batch.status === 'running' && currentStepLabel && (
            <span className="text-xs text-muted-foreground">{currentStepLabel}</span>
          )}
          <Badge
            variant={
              batch.status === 'done' ? 'default' :
              batch.status === 'error' ? 'destructive' :
              batch.status === 'running' ? 'secondary' : 'outline'
            }
          >
            {batch.status === 'pending' && 'Pending'}
            {batch.status === 'running' && 'Running'}
            {batch.status === 'done' && 'Done'}
            {batch.status === 'error' && 'Error'}
          </Badge>
        </div>
      </div>
      {(batch.status === 'running' || batch.steps.length > 0) && (
        <div className="space-y-1">
          <StepProgressBar steps={batch.steps} showLabel />
        </div>
      )}
      {batch.status === 'running' && batch.elapsed > 0 && (
        <div className="text-xs text-muted-foreground">
          {batch.elapsed.toFixed(1)}s elapsed
        </div>
      )}
      {batch.status === 'error' && batch.error && (
        <div className="text-xs text-destructive">Failed: {batch.error}</div>
      )}
      {showRetry && batch.status === 'error' && onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="w-full mt-1">
          <RotateCcw className="size-3.5 mr-1" />
          Retry
        </Button>
      )}
      {batch.conference && (
        <div className="space-y-3 bg-muted/30 rounded-lg p-4 mt-2">
          <div className="text-base font-bold leading-tight">{batch.conference.conference_name}</div>
          {batch.conference.date_start && batch.conference.date_end && (
            <div className="text-sm">
              <span className="text-muted-foreground">Dates: </span>
              <span>{batch.conference.date_start} – {batch.conference.date_end}</span>
            </div>
          )}
          {(batch.conference.venue_city || batch.conference.venue_country) && (
            <div className="text-sm">
              <span className="text-muted-foreground">Venue: </span>
              <span>{[batch.conference.venue_city, batch.conference.venue_country].filter(Boolean).join(', ')}</span>
            </div>
          )}
          {batch.conference && <SpeakerSection conference={batch.conference} />}

          {/* Stats row */}
          {batch.conference && batch.conference.total_speakers > 0 && (
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
          {(batch.conference.fee_range_usd || batch.conference.early_bird_deadline) && (
            <div className="text-sm space-y-0.5">
              {batch.conference.fee_range_usd && (
                <div><span className="text-muted-foreground">Fee: </span><span>{batch.conference.fee_range_usd}</span></div>
              )}
              {batch.conference.early_bird_deadline && (
                <div><span className="text-muted-foreground">Early bird: </span><span>{batch.conference.early_bird_deadline}</span></div>
              )}
            </div>
          )}
          {batch.conference.website_url && (
            <a href={batch.conference.website_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline break-all">
              {batch.conference.website_url}
            </a>
          )}
        </div>
      )}
      {batch.status === 'done' && !batch.conference && (
        <div className="text-xs text-muted-foreground">No conference data extracted</div>
      )}
    </div>
  );
}

export default function DiscoveryPage() {
  const [topic, setTopic] = useState('medical');
  const [monthsAhead, setMonthsAhead] = useState(3);
  const [numResults, setNumResults] = useState(5);
  const { results, isRunning: isDiscoveryRunning, isSearching, foundCount, error: discoveryError, elapsed, startDiscovery, clearResults } =
    useDiscovery();
  const { steps, conference, isRunning: isPipelineRunning, error: pipelineError, startPipeline, cancelPipeline } = usePipeline();
  const { conferences, isRunning: isBatchRunning, totalElapsed, startBatch, cancelBatch, clearResults: clearBatch } = usePipelineBatch();

  const hasRunRef = useRef(false);
  const [expandedUrl, setExpandedUrl] = useState<string | null>(null);
  const [singleExploreUrl, setSingleExploreUrl] = useState<string | null>(null);
  const resultsEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to last result when new ones appear
  useEffect(() => {
    if (results.length > 0 && resultsEndRef.current) {
      resultsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [results.length]);

  // Auto-run on mount only if no stored results exist
  useEffect(() => {
    if (!hasRunRef.current) {
      hasRunRef.current = true;
      // Only auto-run if sessionStorage is empty (user returning to page keeps their results)
      const stored = sessionStorage.getItem('discovery_results');
      if (!stored || JSON.parse(stored).length === 0) {
        startDiscovery(topic, monthsAhead, numResults);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRun = () => {
    startDiscovery(topic, monthsAhead, numResults);
  };

  const handleResultClick = (url: string) => {
    // Navigate to home page with the URL pre-filled
    window.location.href = `/?url=${encodeURIComponent(url)}`;
  };

  const handleExploreSingle = (url: string) => {
    setSingleExploreUrl(url);
    setExpandedUrl(url);
    startPipeline(url);
  };

  const handleCancelSingle = () => {
    cancelPipeline();
    setSingleExploreUrl(null);
    setExpandedUrl(null);
  };

  const handleExploreAll = () => {
    clearBatch();
    startBatch(results.map(r => ({ url: r.url, title: r.title })));
  };

  const handleRetryFailed = () => {
    const failedUrls = Array.from(conferences.values())
      .filter(c => c.status === 'error')
      .map(c => ({ url: c.url, title: c.title }));
    if (failedUrls.length > 0) {
      startBatch(failedUrls);
    }
  };

  const handleCancelBatch = () => {
    cancelBatch();
  };

  const handleToggleExpand = (url: string) => {
    setExpandedUrl(prev => prev === url ? null : url);
  };

  const handleClearBatch = () => {
    clearBatch();
  };

  const isAnyRunning = isDiscoveryRunning || isPipelineRunning || isBatchRunning;
  const hasResults = results.length > 0;
  const hasBatchResults = conferences.size > 0;

  // Count batch results
  const batchSucceeded = Array.from(conferences.values()).filter(c => c.status === 'done' && c.conference).length;
  const batchFailed = Array.from(conferences.values()).filter(c => c.status === 'error').length;
  const batchTotal = conferences.size;

  // Estimate time remaining based on average step time
  const avgStepTime = totalElapsed / (PIPELINE_STEPS.length * batchTotal || 1);
  const remainingConferences = Array.from(conferences.values()).filter(c => c.status === 'running' || c.status === 'pending').length;
  const estimatedRemaining = remainingConferences > 0 ? avgStepTime * PIPELINE_STEPS.length * remainingConferences : 0;

  return (
    <div data-testid="discovery-page" className="discovery-page">
      <nav className="breadcrumb text-sm text-muted-foreground mb-4">
        <Link to="/" className="hover:underline">Home</Link>
        <span className="mx-2">{'›'}</span>
        <span>Discovery</span>
      </nav>

      <h2 className="text-lg font-semibold mb-4">Conference Discovery</h2>
      <p className="text-sm text-muted-foreground mb-4">
        Search for conferences matching your topic using Exa AI + LLM relevance filtering.
        Click a result to run the full extraction pipeline on it.
      </p>

      {/* Search Form */}
      <div className="discovery-form space-y-3 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1">Topic</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. medical, engineering, AI"
            disabled={isAnyRunning}
            data-testid="discovery-topic-input"
            className="url-input"
          />
        </div>
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">
              Months ahead: {monthsAhead}
            </label>
            <input
              type="range"
              min={1}
              max={12}
              value={monthsAhead}
              onChange={(e) => setMonthsAhead(Number(e.target.value))}
              disabled={isAnyRunning}
              data-testid="discovery-months-input"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">
              Results per query: {numResults}
            </label>
            <input
              type="range"
              min={1}
              max={20}
              value={numResults}
              onChange={(e) => setNumResults(Number(e.target.value))}
              disabled={isAnyRunning}
              data-testid="discovery-results-input"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRun}
            disabled={isAnyRunning || !topic.trim()}
            data-testid="discovery-run-button"
            className="btn-run"
          >
            {isDiscoveryRunning ? 'Searching...' : 'Search'}
          </button>
          {hasResults && (
            <button
              onClick={() => { clearResults(); clearBatch(); }}
              disabled={isAnyRunning}
              className="btn-cancel"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {discoveryError && (
        <div className="error-banner mb-4" data-testid="discovery-error">
          <p>{discoveryError}</p>
        </div>
      )}

      {/* Discovery Status — streaming banner */}
      {isSearching && (
        <div className="mb-4 flex items-center gap-2 text-sm text-muted-foreground" data-testid="discovery-loading">
          <Loader2 className="size-4 animate-spin shrink-0" />
          <span>
            Searching Exa + filtering...
            <span className="ml-1 font-medium text-foreground animate-pulse">
              {foundCount} found
            </span>
            {' '}so far ({elapsed.toFixed(1)}s)
          </span>
        </div>
      )}

      {/* Discovery done — static summary */}
      {!isSearching && isDiscoveryRunning && (
        <div className="mb-4 text-sm text-muted-foreground" data-testid="discovery-loading">
          Processing results... ({elapsed.toFixed(1)}s)
        </div>
      )}

      {/* Batch Pipeline Status */}
      {isBatchRunning && (
        <div className="mb-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Exploring all conferences... ({totalElapsed.toFixed(1)}s)
            </div>
            <Button variant="ghost" size="sm" onClick={handleCancelBatch}>
              <X className="size-4 mr-1" />
              Cancel
            </Button>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {Array.from(conferences.values()).map(conf => (
              <BatchStatusCard key={conf.url} batch={conf} showRetry={false} />
            ))}
          </div>
        </div>
      )}

      {/* Batch Complete Summary */}
      {!isBatchRunning && hasBatchResults && (
        <div className="mb-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Batch Complete</span>
              <span className="text-sm text-muted-foreground">
                ({batchSucceeded} succeeded
                {batchFailed > 0 && <span className="text-destructive">, {batchFailed} failed</span>}
                {' '}out of {batchTotal})
              </span>
            </div>
            <div className="flex items-center gap-1">
              {batchFailed > 0 && (
                <Button variant="outline" size="sm" onClick={handleRetryFailed}>
                  <RotateCcw className="size-3.5 mr-1" />
                  Retry ({batchFailed})
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={handleClearBatch}>
                Clear
              </Button>
            </div>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {Array.from(conferences.values()).map(conf => (
              <BatchStatusCard key={conf.url} batch={conf} showRetry={batchFailed > 0} onRetry={handleRetryFailed} />
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {!isDiscoveryRunning && hasResults && !hasBatchResults && (
        <div data-testid="discovery-results">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-muted-foreground">
              {isSearching ? (
                <>
                  <span className="animate-pulse font-medium text-foreground">
                    {foundCount}
                  </span>
                  {' '}found so far
                  {results.length > 0 && ` — ${results.length} shown`}
                  {' '}({elapsed.toFixed(1)}s)
                </>
              ) : (
                <>
                  Found {results.length} conference{results.length !== 1 ? 's' : ''} in {elapsed.toFixed(1)}s
                </>
              )}
            </p>
            {!isBatchRunning && (
              <Button
                variant="default"
                size="sm"
                onClick={handleExploreAll}
                disabled={isAnyRunning}
              >
                <Play className="size-4 mr-1" />
                Explore ALL
              </Button>
            )}
          </div>
          <ul className="space-y-2">
            {results.map((r, idx) => (
              <li key={r.url + idx}>
                <ConferenceResultCard
                  result={r}
                  index={idx}
                  expandedUrl={singleExploreUrl === r.url ? expandedUrl : null}
                  onExplore={() => handleExploreSingle(r.url)}
                  onCancel={handleCancelSingle}
                  onToggleExpand={() => handleToggleExpand(r.url)}
                  pipelineState={
                    singleExploreUrl === r.url
                      ? { steps, conference, isRunning: isPipelineRunning, error: pipelineError }
                      : { steps: [], conference: null, isRunning: false, error: null }
                  }
                />
              </li>
            ))}
            {/* Invisible anchor for auto-scroll to last result */}
            <div ref={resultsEndRef} />
          </ul>
        </div>
      )}

      {!isDiscoveryRunning && results.length === 0 && !discoveryError && hasRunRef.current && (
        <div className="text-sm text-muted-foreground" data-testid="discovery-empty">
          No conferences found. Try broadening the topic or increasing months ahead.
        </div>
      )}
    </div>
  );
}