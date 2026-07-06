// EventSource wrapper with cleanup for the generation stream (§B.7.5).

export const SSE_EVENTS = [
  "agent_started",
  "agent_progress",
  "agent_completed",
  "graph_transition",
  "generation_complete",
  "error",
] as const;

export type SSEEventName = (typeof SSE_EVENTS)[number];

export type SSEHandler = (event: SSEEventName, data: unknown) => void;

export interface StreamOptions {
  onError?: (event: Event) => void;
}

/** Open the SSE stream; returns a dispose function that closes the connection. */
export function openEventStream(
  url: string,
  onEvent: SSEHandler,
  options?: StreamOptions,
): () => void {
  const source = new EventSource(url);

  for (const name of SSE_EVENTS) {
    source.addEventListener(name, (event) => {
      const message = event as MessageEvent<string>;
      let payload: unknown = null;
      try {
        payload = JSON.parse(message.data);
      } catch {
        payload = message.data;
      }
      onEvent(name, payload);
    });
  }

  source.onerror = (event) => {
    options?.onError?.(event);
  };

  return () => source.close();
}
