import { StrictMode } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { CandleStreamHandlers } from "@/lib/candleStream";
import type {
  CandleHistoryResponse,
  CandleInterval,
  ChartPeriod,
  MarketCandle,
  StreamCandleUpdate,
} from "@/lib/marketData";

import { ChartPanel, type ChartPanelProps } from "./ChartPanel";

const firstCandle: MarketCandle = {
  timestamp: "2026-07-24T15:30:00Z",
  open: "210.00",
  high: "210.25",
  low: "209.95",
  close: "210.10",
  volume: 100,
};

function response(overrides: Partial<CandleHistoryResponse> = {}): CandleHistoryResponse {
  return {
    symbol: "AAPL",
    interval: "1m",
    period: "1d",
    timezone: "UTC",
    dataSource: "demo",
    asOf: "2026-07-24T15:30:05Z",
    candles: [firstCandle],
    metadata: {
      state: "SUCCESS",
      code: "MARKET_DATA_CANDLES_SUCCESS",
      recoverable: false,
      retryAfterSeconds: null,
      freshness: {
        providerTimestamp: "2026-07-24T15:30:05Z",
        ingestedAt: "2026-07-24T15:30:05Z",
        delaySeconds: 0,
        state: "FRESH",
      },
      warnings: ["Simulated demo data."],
    },
    ...overrides,
  };
}

function update(overrides: Partial<StreamCandleUpdate> = {}): StreamCandleUpdate {
  return {
    ...firstCandle,
    symbol: "AAPL",
    interval: "1m",
    eventTimestamp: "2026-07-24T15:30:06Z",
    sequence: 1,
    ...overrides,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

function FakeChart({
  candles,
  accessibleLabel,
}: {
  candles: readonly MarketCandle[];
  accessibleLabel: string;
}) {
  return (
    <div data-testid="chart" aria-label={accessibleLabel}>
      {JSON.stringify(candles)}
    </div>
  );
}

function createStreamHarness() {
  const connections: Array<{
    handlers: CandleStreamHandlers;
    close: ReturnType<typeof vi.fn>;
    active: boolean;
  }> = [];
  let activeCount = 0;
  let maxActiveCount = 0;
  const factory = vi.fn<NonNullable<ChartPanelProps["createStream"]>>(
    (_baseUrl, _symbol, _interval, handlers) => {
      activeCount += 1;
      maxActiveCount = Math.max(maxActiveCount, activeCount);
      const connection = {
        handlers,
        active: true,
        close: vi.fn(() => {
          if (connection.active) {
            connection.active = false;
            activeCount -= 1;
          }
        }),
      };
      connections.push(connection);
      return { close: connection.close };
    },
  );
  return {
    connections,
    factory,
    getActiveCount: () => activeCount,
    getMaxActiveCount: () => maxActiveCount,
  };
}

function renderPanel(overrides: Partial<ChartPanelProps> = {}) {
  return render(
    <ChartPanel
      apiBaseUrl="http://api.test"
      symbol="AAPL"
      ChartComponent={FakeChart}
      {...overrides}
    />,
  );
}

describe("ChartPanel", () => {
  it("shows loading, renders history, labels demo data, then starts streaming", async () => {
    const request = deferred<CandleHistoryResponse>();
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockReturnValue(request.promise);
    const stream = createStreamHarness();
    renderPanel({ createStream: stream.factory, fetchHistory });

    expect(screen.getByRole("status")).toHaveTextContent("Loading AAPL chart");
    expect(stream.factory).not.toHaveBeenCalled();

    await act(async () => {
      request.resolve(response());
      await request.promise;
    });

    expect(screen.getByTestId("chart")).toHaveTextContent('"close":"210.10"');
    expect(screen.getByText(/simulated demo data/i)).toBeVisible();
    expect(screen.getByRole("heading", { name: /AAPL.*1m.*1d/i })).toBeVisible();
    expect(stream.factory).toHaveBeenCalledTimes(1);
  });

  it("keeps interval and period independent while disabling invalid combinations", async () => {
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockResolvedValue(response());
    renderPanel({ createStream: createStreamHarness().factory, fetchHistory });
    await screen.findByTestId("chart");

    const interval = screen.getByRole("combobox", { name: "Candle interval" });
    const period = screen.getByRole("combobox", { name: "Chart period" });
    expect(screen.getByRole("option", { name: "1 month" })).toBeDisabled();

    fireEvent.change(interval, { target: { value: "1h" } });
    await waitFor(() => expect(fetchHistory).toHaveBeenCalledTimes(2));
    expect(interval).toHaveValue("1h");
    expect(period).toHaveValue("1d");

    fireEvent.change(period, { target: { value: "3mo" } });
    await waitFor(() => expect(fetchHistory).toHaveBeenCalledTimes(3));
    expect(interval).toHaveValue("1h");
    expect(period).toHaveValue("3mo");

    fireEvent.change(period, { target: { value: "1d" } });
    await waitFor(() => expect(fetchHistory).toHaveBeenCalledTimes(4));
    fireEvent.change(interval, { target: { value: "1d" } });
    await waitFor(() => expect(fetchHistory).toHaveBeenCalledTimes(5));
    expect(interval).toHaveValue("1d");
    expect(period).toHaveValue("1mo");
  });

  it("updates active candles, appends new buckets, and suppresses duplicate or older data", async () => {
    const stream = createStreamHarness();
    renderPanel({
      createStream: stream.factory,
      fetchHistory: vi.fn().mockResolvedValue(response()),
    });
    await screen.findByTestId("chart");
    const handlers = stream.connections[0]!.handlers;

    act(() => {
      handlers.onUpdate(update({ close: "210.20", sequence: 1 }));
      handlers.onUpdate(update({ close: "999.00", sequence: 1 }));
      handlers.onUpdate(
        update({
          timestamp: "2026-07-24T15:29:00Z",
          close: "888.00",
          sequence: 2,
        }),
      );
      handlers.onUpdate(
        update({
          timestamp: "2026-07-24T15:31:00Z",
          open: "210.30",
          high: "210.30",
          low: "210.30",
          close: "210.30",
          sequence: 2,
        }),
      );
    });

    const chart = screen.getByTestId("chart");
    expect(chart).toHaveTextContent('"close":"210.20"');
    expect(chart).toHaveTextContent('"timestamp":"2026-07-24T15:31:00Z"');
    expect(chart).not.toHaveTextContent("999.00");
    expect(chart).not.toHaveTextContent("888.00");
  });

  it("aborts requests and closes streams when parameters change or the panel unmounts", async () => {
    const signals: AbortSignal[] = [];
    const fetchHistory = vi.fn<NonNullable<ChartPanelProps["fetchHistory"]>>(
      (
        _baseUrl: string,
        _symbol: string,
        interval: CandleInterval,
        period: ChartPeriod,
        signal: AbortSignal,
      ) => {
        signals.push(signal);
        return Promise.resolve(response({ interval, period }));
      },
    );
    const stream = createStreamHarness();
    const view = renderPanel({ createStream: stream.factory, fetchHistory });
    await screen.findByTestId("chart");

    fireEvent.change(screen.getByRole("combobox", { name: "Candle interval" }), {
      target: { value: "5m" },
    });
    await waitFor(() => expect(fetchHistory).toHaveBeenCalledTimes(2));

    expect(signals[0]?.aborted).toBe(true);
    expect(stream.connections[0]?.close).toHaveBeenCalledOnce();

    view.unmount();
    expect(signals[1]?.aborted).toBe(true);
    expect(stream.connections[1]?.close).toHaveBeenCalledOnce();
    expect(stream.getActiveCount()).toBe(0);
  });

  it("does not leave simultaneous streams active in React Strict Mode", async () => {
    const stream = createStreamHarness();
    render(
      <StrictMode>
        <ChartPanel
          apiBaseUrl="http://api.test"
          symbol="AAPL"
          ChartComponent={FakeChart}
          createStream={stream.factory}
          fetchHistory={vi.fn().mockResolvedValue(response())}
        />
      </StrictMode>,
    );

    await screen.findByTestId("chart");
    expect(stream.getMaxActiveCount()).toBeLessThanOrEqual(1);
    expect(stream.getActiveCount()).toBe(1);
  });

  it("shows empty history without opening a stream", async () => {
    const stream = createStreamHarness();
    renderPanel({
      createStream: stream.factory,
      fetchHistory: vi.fn().mockResolvedValue(
        response({
          candles: [],
          metadata: {
            ...response().metadata,
            state: "EMPTY",
          },
        }),
      ),
    });

    expect(await screen.findByText(/no candle data is available/i)).toBeVisible();
    expect(stream.factory).not.toHaveBeenCalled();
  });

  it("shows history errors and retries without changing controls", async () => {
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(response());
    renderPanel({ createStream: createStreamHarness().factory, fetchHistory });

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load AAPL chart");
    fireEvent.click(screen.getByRole("button", { name: "Retry chart" }));

    expect(await screen.findByTestId("chart")).toBeVisible();
    expect(screen.getByRole("combobox", { name: "Candle interval" })).toHaveValue("1m");
    expect(screen.getByRole("combobox", { name: "Chart period" })).toHaveValue("1d");
  });

  it("preserves candles for disconnected, terminal, and stale states", async () => {
    const stream = createStreamHarness();
    renderPanel({
      createStream: stream.factory,
      fetchHistory: vi.fn().mockResolvedValue(
        response({
          metadata: {
            ...response().metadata,
            freshness: {
              ...response().metadata.freshness!,
              state: "STALE",
            },
          },
        }),
      ),
    });
    await screen.findByTestId("chart");

    expect(screen.getByText(/data is stale/i)).toBeVisible();
    act(() => stream.connections[0]!.handlers.onDisconnected());
    expect(screen.getByText(/reconnecting/i)).toBeVisible();
    expect(screen.getByTestId("chart")).toBeVisible();

    act(() => stream.connections[0]!.handlers.onError(new Error("exhausted")));
    expect(screen.getByRole("alert")).toHaveTextContent(/updates stopped/i);
    expect(screen.getByTestId("chart")).toBeVisible();
    expect(screen.getByRole("button", { name: "Retry chart" })).toBeVisible();
  });

  it("ignores stale history responses after a parameter change", async () => {
    const first = deferred<CandleHistoryResponse>();
    const second = deferred<CandleHistoryResponse>();
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    renderPanel({ createStream: createStreamHarness().factory, fetchHistory });

    fireEvent.change(screen.getByRole("combobox", { name: "Candle interval" }), {
      target: { value: "5m" },
    });
    await act(async () => {
      second.resolve(
        response({
          interval: "5m",
          candles: [{ ...firstCandle, close: "222.00" }],
        }),
      );
      await second.promise;
    });
    await act(async () => {
      first.resolve(response({ candles: [{ ...firstCandle, close: "111.00" }] }));
      await first.promise;
    });

    expect(screen.getByTestId("chart")).toHaveTextContent("222.00");
    expect(screen.getByTestId("chart")).not.toHaveTextContent("111.00");
  });
});
