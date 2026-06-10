import { useState, useCallback, useRef, useEffect } from 'react';

interface UseDiscoveryReturn {
  results: Array<{ url: string; title: string }>;
  isRunning: boolean;
  isSearching: boolean;   // true while Exa is still querying + filtering
  foundCount: number;     // live count as results trickle in
  error: string | null;
  elapsed: number;
  startDiscovery: (topic: string, monthsAhead: number, numResults: number) => void;
  clearResults: () => void;
}

export function useDiscovery(): UseDiscoveryReturn {
  const [results, setResults] = useState<Array<{ url: string; title: string }>>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [foundCount, setFoundCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
    };
  }, []);

  const startDiscovery = useCallback(
    (topic: string, monthsAhead: number, numResults: number) => {
      setResults([]);
      setError(null);
      setElapsed(0);
      setFoundCount(0);
      setIsSearching(false);
      setIsRunning(true);

      const controller = new AbortController();
      controllerRef.current?.abort();
      controllerRef.current = controller;

      fetch('/api/discovery/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, months_ahead: monthsAhead, num_results: numResults }),
        signal: controller.signal,
      })
        .then(async (res) => {
          if (!res.ok) {
            const text = await res.text().catch(() => 'Unknown error');
            throw new Error(`Discovery ${res.status}: ${text}`);
          }
          const reader = res.body?.getReader();
          if (!reader) throw new Error('No response body');

          const decoder = new TextDecoder();
          let buffer = '';

          (async () => {
            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                buffer = buffer.replace(/\r\n/g, '\n');
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (const part of parts) {
                  if (!part.trim()) continue;
                  const eventMatch = part.match(/^event: (.+)$/m);
                  const dataMatch = part.match(/^data: (.+)$/m);
                  const eventType = eventMatch?.[1];
                  const rawData = dataMatch?.[1];
                  if (!eventType || !rawData) continue;

                  switch (eventType) {
                    case 'search_start': {
                      setIsSearching(true);
                      const d = JSON.parse(rawData);
                      if (d.elapsed) setElapsed(d.elapsed);
                      break;
                    }

                    case 'result_found': {
                      const d = JSON.parse(rawData);
                      setFoundCount(d.count);
                      setElapsed(d.elapsed);
                      if (d.item) {
                        setResults(prev => [...prev, d.item]);
                      }
                      break;
                    }

                    case 'search_complete': {
                      setIsSearching(false);
                      const d = JSON.parse(rawData);
                      setElapsed(d.total_elapsed);
                      setIsRunning(false);
                      break;
                    }

                    case 'step_complete': {
                      const d = JSON.parse(rawData);
                      if (d.elapsed) setElapsed(d.elapsed);
                      if (d.step === 'error') {
                        setError(d.error);
                      }
                      break;
                    }

                    case 'done':
                      setIsRunning(false);
                      break;
                  }
                }
              }
            } catch (err: unknown) {
              if (err instanceof Error && err.name === 'AbortError') return;
              setError(err instanceof Error ? err.message : String(err));
              setIsRunning(false);
            }
          })();
        })
        .catch((err) => {
          if (err instanceof Error && err.name !== 'AbortError') {
            setError(err.message);
          }
          setIsRunning(false);
        });
    },
    [],
  );

  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
    setElapsed(0);
    setFoundCount(0);
  }, []);

  return {
    results,
    isRunning,
    isSearching,
    foundCount,
    error,
    elapsed,
    startDiscovery,
    clearResults,
  };
}