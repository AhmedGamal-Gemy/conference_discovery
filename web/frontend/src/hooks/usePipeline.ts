import { useState, useCallback, useRef, useEffect } from 'react';
import { connectPipelineSSE, type SSEConnection } from '../api/sse';
import type { PipelineStep, StepStartData, StepCompleteData, StepErrorData, PipelineCompleteData } from '../types/pipeline';
import type { Conference } from '../types/conference';

interface UsePipelineReturn {
  steps: PipelineStep[];
  conference: Conference | null;
  isRunning: boolean;
  error: string | null;
  startPipeline: (url: string) => void;
  cancelPipeline: () => void;
}

export function usePipeline(): UsePipelineReturn {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [conference, setConference] = useState<Conference | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const connectionRef = useRef<SSEConnection | null>(null);

  useEffect(() => {
    return () => {
      connectionRef.current?.abort();
    };
  }, []);

  const startPipeline = useCallback((url: string) => {
    setSteps([]);
    setConference(null);
    setError(null);
    setIsRunning(true);

    connectionRef.current?.abort();

    connectPipelineSSE(url, {
      onStepStart: (data: StepStartData) => {
        setSteps(prev => [...prev, { ...data, status: 'start', error: null }]);
      },
      onStepComplete: (data: StepCompleteData) => {
        setSteps(prev => prev.map(s =>
          s.step === data.step ? { ...s, ...data, status: 'complete' as const } : s
        ));
      },
      onStepError: (data: StepErrorData) => {
        setSteps(prev => prev.map(s =>
          s.step === data.step ? { ...s, ...data, status: 'error' as const, error: data.error } : s
        ));
      },
      onPipelineComplete: (data: PipelineCompleteData) => {
        if (data.conference) {
          setConference(data.conference);
        }
      },
      onDone: () => {
        setIsRunning(false);
      },
      onError: (err: Error) => {
        setError(err.message);
        setIsRunning(false);
      },
    }).then(conn => {
      connectionRef.current = conn;
    });
  }, []);

  const cancelPipeline = useCallback(() => {
    connectionRef.current?.abort();
    connectionRef.current = null;
    setIsRunning(false);
  }, []);

  return { steps, conference, isRunning, error, startPipeline, cancelPipeline };
}
