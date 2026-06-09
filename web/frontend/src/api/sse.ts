import type {
  StepStartData,
  StepCompleteData,
  StepErrorData,
  PipelineCompleteData,
} from '../types/pipeline';

export interface SSECallbacks {
  onStepStart?: (data: StepStartData) => void;
  onStepComplete?: (data: StepCompleteData) => void;
  onStepError?: (data: StepErrorData) => void;
  onPipelineComplete?: (data: PipelineCompleteData) => void;
  onDone?: () => void;
  onError?: (error: Error) => void;
}

export interface SSEConnection {
  abort: () => void;
}

export async function connectPipelineSSE(
  url: string,
  callbacks: SSECallbacks,
  user_id: string = 'web_user',
): Promise<SSEConnection> {
  const controller = new AbortController();

  const response = await fetch('/api/pipeline/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, user_id }),
    signal: controller.signal,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => 'Unknown error');
    callbacks.onError?.(new Error(`SSE ${response.status}: ${text}`));
    return { abort: () => controller.abort() };
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError?.(new Error('No response body'));
    return { abort: () => controller.abort() };
  }

  const decoder = new TextDecoder();
  let buffer = '';

  (async () => {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // Normalize \r\n → \n: sse_starlette uses \r\n as default line separator
        buffer = buffer.replace(/\r\n/g, '\n');
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;
          const eventMatch = part.match(/^event: (.+)$/m);
          const dataMatch = part.match(/^data: (.+)$/m);
          const eventType = eventMatch?.[1];
          const rawData = dataMatch?.[1];

          switch (eventType) {
            case 'step_start':
              callbacks.onStepStart?.(JSON.parse(rawData!));
              break;
            case 'step_complete':
              callbacks.onStepComplete?.(JSON.parse(rawData!));
              break;
            case 'step_error':
              callbacks.onStepError?.(JSON.parse(rawData!));
              break;
            case 'pipeline_complete':
              callbacks.onPipelineComplete?.(JSON.parse(rawData!));
              break;
            case 'done':
              callbacks.onDone?.();
              break;
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return { abort: () => controller.abort() };
}
