import { useState, useCallback, useRef, useEffect } from 'react';
import type { DiscoveryEvent, DiscoveryCompleteData } from '../types/pipeline';

interface UseDiscoveryReturn {
  results: Array<{ url: string; title: string }>;
  isRunning: boolean;
  error: string | null;
  elapsed: number;
  startDiscovery: (topic: string, monthsAhead: number, numResults: number) => void;
  clearResults: () => void;
}

export function useDiscovery(): UseDiscoveryReturn {
  const [results, setResults] = useState<Array<{ url: string; title: string }>>([]);
  const [isRunning, setIsRunning] = useState(false);
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
                    case 'step_complete': {
                      const d = JSON.parse(rawData);
                      if (d.elapsed) setElapsed(d.elapsed);
                      break;
                    }
                    case 'pipeline_complete': {
                      const d = JSON.parse(rawData) as DiscoveryCompleteData;
                      setResults(d.results || []);
                      setElapsed(d.total_elapsed);
                      setIsRunning(false);
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
  }, []);

  return { results, isRunning, error, elapsed, startDiscovery, clearResults };
}
