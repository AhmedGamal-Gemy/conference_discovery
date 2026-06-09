import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  BatchStartedData,
  ConferenceStartData,
  StepStartData,
  StepCompleteData,
  StepErrorData,
  ConferenceCompleteData,
  ConferenceErrorData,
  BatchCompleteData,
  PipelineStep,
  PipelineCompleteData,
} from '../types/pipeline';
import type { Conference } from '../types/conference';

export interface BatchConference {
  url: string;
  title: string;
  status: 'pending' | 'running' | 'done' | 'error';
  steps: PipelineStep[];
  conference: Conference | null;
  error: string | null;
  elapsed: number;
}

interface UsePipelineBatchReturn {
  conferences: Map<string, BatchConference>;
  isRunning: boolean;
  totalElapsed: number;
  startBatch: (urls: Array<{ url: string; title?: string }>) => void;
  cancelBatch: () => void;
  clearResults: () => void;
}

export function usePipelineBatch(): UsePipelineBatchReturn {
  const [conferences, setConferences] = useState<Map<string, BatchConference>>(new Map());
  const [isRunning, setIsRunning] = useState(false);
  const [totalElapsed, setTotalElapsed] = useState(0);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
    };
  }, []);

  const startBatch = useCallback((urls: Array<{ url: string; title?: string }>) => {
    setConferences(new Map());
    setTotalElapsed(0);
    setIsRunning(true);

    const controller = new AbortController();
    controllerRef.current?.abort();
    controllerRef.current = controller;

    // Initialize all conferences as pending
    const initial = new Map<string, BatchConference>();
    for (const { url, title } of urls) {
      initial.set(url, {
        url,
        title: title || url,
        status: 'pending',
        steps: [],
        conference: null,
        error: null,
        elapsed: 0,
      });
    }
    setConferences(initial);

    fetch('/api/pipeline/run-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls: urls.map(u => u.url) }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text().catch(() => 'Unknown error');
          throw new Error(`Batch ${res.status}: ${text}`);
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

                setConferences(prev => {
                  const next = new Map(prev);

                  switch (eventType) {
                    case 'batch_started': {
                      const d = JSON.parse(rawData) as BatchStartedData;
                      setTotalElapsed(d.elapsed);
                      break;
                    }

                    case 'conference_start': {
                      const d = JSON.parse(rawData) as ConferenceStartData;
                      const existing = next.get(d.url);
                      if (existing) {
                        next.set(d.url, { ...existing, status: 'running', elapsed: d.elapsed });
                      }
                      setTotalElapsed(d.elapsed);
                      break;
                    }

                    case 'step_start': {
                      const d = JSON.parse(rawData) as StepStartData;
                      const conf = next.get(d.url);
                      if (conf) {
                        const steps = [...conf.steps, { ...d, status: 'start' as const, error: null }];
                        next.set(d.url, { ...conf, steps, elapsed: d.elapsed });
                      }
                      break;
                    }

                    case 'step_complete': {
                      const d = JSON.parse(rawData) as StepCompleteData;
                      const conf = next.get(d.url);
                      if (conf) {
                        const steps = conf.steps.map(s =>
                          s.step === d.step ? { ...s, ...d, status: 'complete' as const } : s
                        );
                        next.set(d.url, { ...conf, steps, elapsed: d.elapsed });
                      }
                      break;
                    }

                    case 'step_error': {
                      const d = JSON.parse(rawData) as StepErrorData;
                      const conf = next.get(d.url);
                      if (conf) {
                        const steps = conf.steps.map(s =>
                          s.step === d.step ? { ...s, ...d, status: 'error' as const, error: d.error } : s
                        );
                        next.set(d.url, { ...conf, steps, error: d.error, elapsed: d.elapsed });
                      }
                      break;
                    }

                    case 'conference_complete': {
                      const d = JSON.parse(rawData) as ConferenceCompleteData;
                      const conf = next.get(d.url);
                      if (conf) {
                        next.set(d.url, {
                          ...conf,
                          status: 'done',
                          conference: d.conference as Conference | null,
                          elapsed: d.elapsed,
                          error: null,
                        });
                      }
                      break;
                    }

                    case 'conference_error': {
                      const d = JSON.parse(rawData) as ConferenceErrorData;
                      const conf = next.get(d.url);
                      if (conf) {
                        next.set(d.url, {
                          ...conf,
                          status: 'error',
                          error: d.error,
                          elapsed: d.elapsed,
                        });
                      }
                      break;
                    }

                    case 'batch_complete': {
                      const d = JSON.parse(rawData) as BatchCompleteData;
                      setTotalElapsed(d.elapsed);
                      break;
                    }
                  }

                  return next;
                });

                if (eventType === 'done' || eventType === 'batch_complete') {
                  setIsRunning(false);
                }
              }
            }
          } catch (err: unknown) {
            if (err instanceof Error && err.name === 'AbortError') return;
            setIsRunning(false);
          }
        })();
      })
      .catch((err) => {
        if (err instanceof Error && err.name !== 'AbortError') {
          console.error('Batch error:', err.message);
        }
        setIsRunning(false);
      });
  }, []);

  const cancelBatch = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setIsRunning(false);
  }, []);

  const clearResults = useCallback(() => {
    setConferences(new Map());
    setTotalElapsed(0);
  }, []);

  return { conferences, isRunning, totalElapsed, startBatch, cancelBatch, clearResults };
}