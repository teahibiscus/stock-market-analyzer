import { describe, expect, it, vi } from "vitest";

import {
  createCandleStream,
  type CandleEventSource,
  type CandleStreamHandlers,
  type CandleStreamOptions,
} from "./candleStream";
import type { StreamCandleUpdate } from "./marketData";

const validUpdate: StreamCandleUpdate = {
  symbol: "AAPL",
  interval: "1m",
  timestamp: "2026-07-24T15:30:00Z",
  open: "210.0100",
  high: "210.2500",
  low: "209.9900",
  close: "210.1250",
  volume: 1234,
  eventTimestamp: "2026-07-24T15:30:06Z",
  sequence: 1,
};

type Listener = (event: Event | MessageEvent<string>) => void;

class FakeEventSource implements CandleEventSource {
  readonly listeners = new Map<string, Listener[]>();
  close = vi.fn();

  addEventListener(type: string, listener: Listener): void {
    const listeners = this.listeners.get(type) ?? [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  emit(type: string, event: Event | MessageEvent<string> = new Event(type)): void {
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }
}

type ScheduledTask = {
  callback: () => void;
  delay: number;
  cancelled: boolean;
};

function setup(options: Partial<CandleStreamOptions> = {}) {
  const sources: FakeEventSource[] = [];
  const urls: string[] = [];
  const tasks: ScheduledTask[] = [];
  const handlers: CandleStreamHandlers = {
    onOpen: vi.fn(),
    onUpdate: vi.fn(),
    onDisconnected: vi.fn(),
    onError: vi.fn(),
  };
  const eventSourceFactory = (url: string): CandleEventSource => {
    urls.push(url);
    const source = new FakeEventSource();
    sources.push(source);
    return source;
  };
  const schedule = (callback: () => void, delay: number): ScheduledTask => {
    const task = { callback, delay, cancelled: false };
    tasks.push(task);
    return task;
  };
  const cancelScheduled = (handle: unknown): void => {
    (handle as ScheduledTask).cancelled = true;
  };

  const stream = createCandleStream("http://127.0.0.1:8000/", " aapl ", "1m", handlers, {
    eventSourceFactory,
    schedule,
    cancelScheduled,
    initialReconnectDelayMilliseconds: 100,
    maxReconnectAttempts: 3,
    maxReconnectDelayMilliseconds: 250,
    ...options,
  });

  return { handlers, sources, stream, tasks, urls };
}

function runTask(task: ScheduledTask): void {
  if (!task.cancelled) {
    task.callback();
  }
}

describe("createCandleStream", () => {
  it("opens one canonical EventSource and forwards open events", () => {
    const { handlers, sources, urls } = setup();

    expect(urls).toEqual([
      "http://127.0.0.1:8000/api/v1/market-data/stream?symbol=AAPL&interval=1m",
    ]);
    expect(sources).toHaveLength(1);

    sources[0]?.emit("open");

    expect(handlers.onOpen).toHaveBeenCalledTimes(1);
  });

  it("forwards valid candle events and suppresses malformed or unrelated events", () => {
    const { handlers, sources } = setup();
    const source = sources[0]!;

    source.emit("candle", new MessageEvent("candle", { data: JSON.stringify(validUpdate) }));
    source.emit("candle", new MessageEvent("candle", { data: "{invalid" }));
    source.emit("candle", new MessageEvent("candle", { data: JSON.stringify({ sequence: 2 }) }));
    source.emit("message", new MessageEvent("message", { data: JSON.stringify(validUpdate) }));

    expect(handlers.onUpdate).toHaveBeenCalledOnce();
    expect(handlers.onUpdate).toHaveBeenCalledWith(validUpdate);
  });

  it("closes a failed source before reconnecting without duplicate active connections", () => {
    const { handlers, sources, tasks } = setup();
    const failedSource = sources[0]!;

    failedSource.emit("error");

    expect(failedSource.close).toHaveBeenCalledOnce();
    expect(handlers.onDisconnected).toHaveBeenCalledOnce();
    expect(tasks).toHaveLength(1);
    expect(tasks[0]?.delay).toBe(100);
    expect(sources).toHaveLength(1);

    failedSource.emit("error");
    expect(tasks).toHaveLength(1);

    runTask(tasks[0]!);
    expect(sources).toHaveLength(2);
  });

  it("uses bounded exponential backoff and stops after the maximum attempts", () => {
    const { handlers, sources, tasks } = setup();

    sources[0]!.emit("error");
    runTask(tasks[0]!);
    sources[1]!.emit("error");
    runTask(tasks[1]!);
    sources[2]!.emit("error");
    runTask(tasks[2]!);
    sources[3]!.emit("error");

    expect(tasks.map((task) => task.delay)).toEqual([100, 200, 250]);
    expect(sources).toHaveLength(4);
    expect(handlers.onError).toHaveBeenCalledOnce();
  });

  it("closes idempotently, cancels reconnects, and never reconnects afterward", () => {
    const { sources, stream, tasks } = setup();
    const source = sources[0]!;
    source.emit("error");

    stream.close();
    stream.close();

    expect(tasks[0]?.cancelled).toBe(true);
    expect(source.close).toHaveBeenCalledOnce();

    runTask(tasks[0]!);
    expect(sources).toHaveLength(1);
  });
});
