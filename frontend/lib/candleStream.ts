import { CANDLE_INTERVALS, type CandleInterval, type StreamCandleUpdate } from "./marketData";

export type CandleEventListener = (event: Event | MessageEvent<string>) => void;

export interface CandleEventSource {
  addEventListener(type: string, listener: CandleEventListener): void;
  close(): void;
}

export type CandleStreamHandlers = {
  onOpen: () => void;
  onUpdate: (update: StreamCandleUpdate) => void;
  onDisconnected: () => void;
  onError: (error: Error) => void;
};

export type CandleStreamOptions = {
  eventSourceFactory?: (url: string) => CandleEventSource;
  schedule?: (callback: () => void, delayMilliseconds: number) => unknown;
  cancelScheduled?: (handle: unknown) => void;
  maxReconnectAttempts?: number;
  initialReconnectDelayMilliseconds?: number;
  maxReconnectDelayMilliseconds?: number;
};

export type CandleStream = {
  close: () => void;
};

export function createCandleStream(
  baseUrl: string,
  symbol: string,
  interval: CandleInterval,
  handlers: CandleStreamHandlers,
  options: CandleStreamOptions = {},
): CandleStream {
  const eventSourceFactory = options.eventSourceFactory ?? defaultEventSourceFactory;
  const schedule = options.schedule ?? defaultSchedule;
  const cancelScheduled = options.cancelScheduled ?? defaultCancelScheduled;
  const maxReconnectAttempts = options.maxReconnectAttempts ?? 3;
  const initialReconnectDelayMilliseconds = options.initialReconnectDelayMilliseconds ?? 1_000;
  const maxReconnectDelayMilliseconds = options.maxReconnectDelayMilliseconds ?? 30_000;
  const url = new URL(`${baseUrl.replace(/\/$/, "")}/api/v1/market-data/stream`);
  url.searchParams.set("symbol", symbol.trim().toUpperCase());
  url.searchParams.set("interval", interval);

  let activeSource: CandleEventSource | null = null;
  let reconnectHandle: unknown = null;
  let reconnectAttempts = 0;
  let closed = false;

  function connect(): void {
    if (closed || activeSource !== null) {
      return;
    }

    const source = eventSourceFactory(url.toString());
    activeSource = source;

    source.addEventListener("open", () => {
      if (closed || activeSource !== source) {
        return;
      }
      reconnectAttempts = 0;
      handlers.onOpen();
    });

    source.addEventListener("candle", (event) => {
      if (closed || activeSource !== source) {
        return;
      }
      const update = parseCandleUpdate(event);
      if (update !== null) {
        handlers.onUpdate(update);
      }
    });

    source.addEventListener("error", () => {
      if (closed || activeSource !== source) {
        return;
      }

      source.close();
      activeSource = null;
      handlers.onDisconnected();

      if (reconnectAttempts >= maxReconnectAttempts) {
        handlers.onError(new Error("Candle stream reconnect attempts exhausted."));
        return;
      }

      const delay = Math.min(
        initialReconnectDelayMilliseconds * 2 ** reconnectAttempts,
        maxReconnectDelayMilliseconds,
      );
      reconnectAttempts += 1;
      reconnectHandle = schedule(() => {
        reconnectHandle = null;
        connect();
      }, delay);
    });
  }

  connect();

  return {
    close(): void {
      if (closed) {
        return;
      }
      closed = true;
      if (reconnectHandle !== null) {
        cancelScheduled(reconnectHandle);
        reconnectHandle = null;
      }
      activeSource?.close();
      activeSource = null;
    },
  };
}

function parseCandleUpdate(event: Event | MessageEvent<string>): StreamCandleUpdate | null {
  if (!("data" in event) || typeof event.data !== "string") {
    return null;
  }

  try {
    const candidate: unknown = JSON.parse(event.data);
    return isStreamCandleUpdate(candidate) ? candidate : null;
  } catch {
    return null;
  }
}

function isStreamCandleUpdate(value: unknown): value is StreamCandleUpdate {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.symbol === "string" &&
    typeof candidate.interval === "string" &&
    CANDLE_INTERVALS.includes(candidate.interval as CandleInterval) &&
    typeof candidate.timestamp === "string" &&
    typeof candidate.open === "string" &&
    typeof candidate.high === "string" &&
    typeof candidate.low === "string" &&
    typeof candidate.close === "string" &&
    typeof candidate.volume === "number" &&
    Number.isFinite(candidate.volume) &&
    typeof candidate.eventTimestamp === "string" &&
    typeof candidate.sequence === "number" &&
    Number.isInteger(candidate.sequence) &&
    candidate.sequence > 0
  );
}

function defaultEventSourceFactory(url: string): CandleEventSource {
  return new EventSource(url);
}

function defaultSchedule(callback: () => void, delayMilliseconds: number): unknown {
  return globalThis.setTimeout(callback, delayMilliseconds);
}

function defaultCancelScheduled(handle: unknown): void {
  globalThis.clearTimeout(handle as ReturnType<typeof setTimeout>);
}
