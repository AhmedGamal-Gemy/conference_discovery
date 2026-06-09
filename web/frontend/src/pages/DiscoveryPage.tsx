import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useDiscovery } from '../hooks/useDiscovery';

export default function DiscoveryPage() {
  const [topic, setTopic] = useState('medical');
  const [monthsAhead, setMonthsAhead] = useState(3);
  const [numResults, setNumResults] = useState(5);
  const { results, isRunning, error, elapsed, startDiscovery, clearResults } =
    useDiscovery();
  const hasRunRef = useRef(false);

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

  return (
    <div data-testid="discovery-page" className="discovery-page">
      <nav className="breadcrumb text-sm text-muted-foreground mb-4">
        <Link to="/" className="hover:underline">Home</Link>
        <span className="mx-2">&gt;</span>
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
            disabled={isRunning}
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
              disabled={isRunning}
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
              disabled={isRunning}
              data-testid="discovery-results-input"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRun}
            disabled={isRunning || !topic.trim()}
            data-testid="discovery-run-button"
            className="btn-run"
          >
            {isRunning ? 'Searching...' : 'Search'}
          </button>
          {results.length > 0 && (
            <button
              onClick={clearResults}
              disabled={isRunning}
              className="btn-cancel"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="error-banner mb-4" data-testid="discovery-error">
          <p>{error}</p>
        </div>
      )}

      {/* Status */}
      {isRunning && (
        <div className="mb-4 text-sm text-muted-foreground" data-testid="discovery-loading">
          Searching Exa and filtering results... ({elapsed.toFixed(1)}s)
        </div>
      )}

      {/* Results */}
      {!isRunning && results.length > 0 && (
        <div data-testid="discovery-results">
          <p className="text-sm text-muted-foreground mb-3">
            Found {results.length} conference{results.length !== 1 ? 's' : ''} in {elapsed.toFixed(1)}s
          </p>
          <ul className="space-y-2">
            {results.map((r, idx) => (
              <li key={r.url + idx}>
                <button
                  onClick={() => handleResultClick(r.url)}
                  data-testid={`discovery-result-${idx}`}
                  className="w-full text-left p-3 rounded-lg border border-border
                             hover:border-primary hover:bg-accent transition-colors"
                >
                  <div className="font-medium truncate">{r.title || r.url}</div>
                  <div className="text-xs text-muted-foreground truncate">{r.url}</div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isRunning && results.length === 0 && !error && hasRunRef.current && (
        <div className="text-sm text-muted-foreground" data-testid="discovery-empty">
          No conferences found. Try broadening the topic or increasing months ahead.
        </div>
      )}
    </div>
  );
}
