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
} from '../types/pipeline';
import type { Conference } from '../types/conference';
import type { ValidationResult } from '../types/pipeline';

export interface BatchConference {
  url: string;
  title: string;
  status: 'pending' | 'running' | 'done' | 'error';
  steps: PipelineStep[];
  conference: Conference | null;
  validation: ValidationResult | null;
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

const STORAGE_KEY = 'discovery_batch';
const RUNNING_KEY = 'discovery_batch_running';

function loadStoredBatch(): Map<string, BatchConference> {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) return new Map(JSON.parse(stored));
  } catch { /* ignore */ }
  return new Map();
}

function loadStoredRunning(): boolean {
  try {
    return sessionStorage.getItem(RUNNING_KEY) === 'true';
  } catch { return false; }
}

export function usePipelineBatch(): UsePipelineBatchReturn {
  const [conferences, setConferences] = useState<Map<string, BatchConference>>(() => loadStoredBatch());
  const [isRunning, setIsRunning] = useState(() => loadStoredRunning());
  const [totalElapsed, setTotalElapsed] = useState(0);
  const controllerRef = useRef<AbortController | null>(null);

  // Persist to sessionStorage on change
  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...conferences.entries()]));
  }, [conferences]);

  useEffect(() => {
    sessionStorage.setItem(RUNNING_KEY, String(isRunning));
  }, [isRunning]);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
    };
  }, []);

  const startBatch = useCallback((urls: Array<{ url: string; title?: string }>) => {
    sessionStorage.removeItem(STORAGE_KEY);
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
        validation: null,
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
                    case 'conference_start': {
                      const d = JSON.parse(rawData) as ConferenceStartData;
                      const existing = next.get(d.url);
                      if (existing) {
                        next.set(d.url, { ...existing, status: 'running', elapsed: d.elapsed ?? 0, validation: null });
                      }
                      setTotalElapsed(d.elapsed ?? 0);
                      break;
                    }

                    case 'step_start': {
                      const d = JSON.parse(rawData) as StepStartData;
                      const urlKey = d.url ?? '';
                      const conf = next.get(urlKey);
                      if (conf && urlKey) {
                        const steps = [...conf.steps, { ...d, status: 'start' as const, error: null, elapsed: d.elapsed ?? 0 }];
                        next.set(urlKey, { ...conf, steps, elapsed: d.elapsed ?? 0 });
                      }
                      break;
                    }

                    case 'step_complete': {
                      const d = JSON.parse(rawData) as StepCompleteData;
                      const urlKey = d.url ?? '';
                      const conf = next.get(urlKey);
                      if (conf && urlKey) {
                        const steps = conf.steps.map(s =>
                          s.step === d.step ? { ...s, ...d, status: 'complete' as const } : s
                        );
                        next.set(urlKey, { ...conf, steps, elapsed: d.elapsed ?? 0 });
                      }
                      break;
                    }

                    case 'step_error': {
                      const d = JSON.parse(rawData) as StepErrorData;
                      const urlKey = d.url ?? '';
                      const conf = next.get(urlKey);
                      if (conf && urlKey) {
                        const steps = conf.steps.map(s =>
                          s.step === d.step ? { ...s, ...d, status: 'error' as const, error: d.error } : s
                        );
                        next.set(urlKey, { ...conf, steps, error: d.error, elapsed: d.elapsed ?? 0 });
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
                          validation: d.validation as ValidationResult | null,
                          elapsed: d.elapsed ?? 0,
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
                          elapsed: d.elapsed ?? 0,
                        });
                      }
                      break;
                    }

                    case 'batch_started': {
                      const d = JSON.parse(rawData) as BatchStartedData;
                      setTotalElapsed(d.elapsed ?? 0);
                      break;
                    }

                    case 'batch_complete': {
                      const d = JSON.parse(rawData) as BatchCompleteData;
                      setTotalElapsed(d.elapsed ?? 0);
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
    sessionStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(RUNNING_KEY);
    setConferences(new Map());
    setTotalElapsed(0);
    setIsRunning(false);
  }, []);

  return { conferences, isRunning, totalElapsed, startBatch, cancelBatch, clearResults };
}