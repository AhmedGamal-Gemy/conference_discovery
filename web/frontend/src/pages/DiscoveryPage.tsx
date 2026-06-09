import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useDiscovery } from '../hooks/useDiscovery';
import { usePipeline } from '../hooks/usePipeline';
import { usePipelineBatch, type BatchConference } from '../hooks/usePipelineBatch';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Play, X, ChevronDown, ChevronRight, CheckCircle2, Circle, XCircle, Loader2 } from 'lucide-react';
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

function StepIndicator({ steps, step }: { steps: PipelineStep[]; step: string }) {
  const stepData = steps.find(s => s.step === step);
  if (!stepData) return <Circle className="size-3.5 text-muted-foreground/40" />;
  if (stepData.status === 'complete') return <CheckCircle2 className="size-3.5 text-green-500" />;
  if (stepData.status === 'error') return <XCircle className="size-3.5 text-destructive" />;
  return <Loader2 className="size-3.5 text-primary animate-spin" />;
}

function StepProgressBar({ steps }: { steps: PipelineStep[] }) {
  return (
    <div className="flex items-center gap-1">
      {PIPELINE_STEPS.map(step => (
        <div key={step} title={step} className="flex items-center">
          <StepIndicator steps={steps} step={step} />
        </div>
      ))}
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
          <div className="font-medium truncate">{result.title || result.url}</div>
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
              <div className="text-xs text-muted-foreground">Pipeline running...</div>
              <StepProgressBar steps={steps} />
            </div>
          )}
          {error && (
            <div className="text-xs text-destructive">Error: {error}</div>
          )}
          {conference && (
            <div className="space-y-1 text-xs">
              <div className="font-medium">{conference.conference_name}</div>
              <div className="text-muted-foreground">
                {conference.date_start && conference.date_end
                  ? `${conference.date_start} – ${conference.date_end}`
                  : 'Dates TBD'}
              </div>
              <div className="text-muted-foreground">
                {conference.venue_city ? `${conference.venue_city}, ${conference.venue_country || ''}` : 'Venue TBD'}
              </div>
              <div className="text-muted-foreground">
                {conference.total_speakers} speaker{conference.total_speakers !== 1 ? 's' : ''} confirmed
              </div>
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

function BatchStatusCard({ batch }: { batch: BatchConference }) {
  return (
    <div className="border border-border rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <div className="font-medium text-sm truncate">{batch.title || batch.url}</div>
          <div className="text-xs text-muted-foreground truncate">{batch.url}</div>
        </div>
        <Badge
          variant={
            batch.status === 'done' ? 'default' :
            batch.status === 'error' ? 'destructive' :
            batch.status === 'running' ? 'secondary' : 'outline'
          }
          className="ml-2 shrink-0"
        >
          {batch.status === 'pending' && 'Pending'}
          {batch.status === 'running' && 'Running'}
          {batch.status === 'done' && 'Done'}
          {batch.status === 'error' && 'Error'}
        </Badge>
      </div>
      {(batch.status === 'running' || batch.steps.length > 0) && (
        <StepProgressBar steps={batch.steps} />
      )}
      {batch.status === 'error' && batch.error && (
        <div className="text-xs text-destructive">Failed: {batch.error}</div>
      )}
      {batch.conference && (
        <div className="space-y-1 text-xs bg-muted/30 rounded p-2">
          <div className="font-medium">{batch.conference.conference_name}</div>
          <div className="text-muted-foreground">
            {batch.conference.date_start && batch.conference.date_end
              ? `${batch.conference.date_start} – ${batch.conference.date_end}`
              : 'Dates TBD'}
          </div>
          <div className="text-muted-foreground">
            {batch.conference.venue_city ? `${batch.conference.venue_city}, ${batch.conference.venue_country || ''}` : 'Venue TBD'}
          </div>
          <div className="text-muted-foreground">
            {batch.conference.total_speakers} speaker{batch.conference.total_speakers !== 1 ? 's' : ''} confirmed
          </div>
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
  const { results, isRunning: isDiscoveryRunning, error: discoveryError, elapsed, startDiscovery, clearResults } =
    useDiscovery();
  const { steps, conference, isRunning: isPipelineRunning, error: pipelineError, startPipeline, cancelPipeline } = usePipeline();
  const { conferences, isRunning: isBatchRunning, totalElapsed, startBatch, cancelBatch, clearResults: clearBatch } = usePipelineBatch();

  const hasRunRef = useRef(false);
  const [expandedUrl, setExpandedUrl] = useState<string | null>(null);
  const [singleExploreUrl, setSingleExploreUrl] = useState<string | null>(null);

  // Auto-run on mount using settings defaults
  useEffect(() => {
    if (!hasRunRef.current) {
      hasRunRef.current = true;
      startDiscovery(topic, monthsAhead, numResults);
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

  return (
    <div data-testid="discovery-page" className="discovery-page">
      <nav className="breadcrumb text-sm text-muted-foreground mb-4">
        <Link to="/" className="hover:underline">Home</Link>
        <span className="mx-2">></span>
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

      {/* Discovery Status */}
      {isDiscoveryRunning && (
        <div className="mb-4 text-sm text-muted-foreground" data-testid="discovery-loading">
          Searching Exa and filtering results... ({elapsed.toFixed(1)}s)
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
              <BatchStatusCard key={conf.url} batch={conf} />
            ))}
          </div>
        </div>
      )}

      {/* Batch Complete Summary */}
      {!isBatchRunning && hasBatchResults && (
        <div className="mb-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">
              Batch Complete
              <span className="ml-2 text-muted-foreground font-normal">
                ({batchSucceeded} succeeded, {batchFailed} failed out of {batchTotal})
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={handleClearBatch}>
              Clear
            </Button>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {Array.from(conferences.values()).map(conf => (
              <BatchStatusCard key={conf.url} batch={conf} />
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {!isDiscoveryRunning && hasResults && !hasBatchResults && (
        <div data-testid="discovery-results">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-muted-foreground">
              Found {results.length} conference{results.length !== 1 ? 's' : ''} in {elapsed.toFixed(1)}s
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