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
  showVolume,
}: {
  candles: readonly MarketCandle[];
  accessibleLabel: string;
  showVolume?: boolean;
}) {
  return (
    <div data-testid="chart" aria-label={accessibleLabel} data-show-volume={String(showVolume)}>
      {JSON.stringify(candles)}
    </div>
  );
}

function InspectableChart({
  candles,
  onInspectionChange,
}: {
  candles: readonly MarketCandle[];
  onInspectionChange?: (candle: MarketCandle | null) => void;
}) {
  return (
    <button type="button" onClick={() => onInspectionChange?.(candles[0] ?? null)}>
      Inspect candle
    </button>
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
      instrumentId="instrument-aapl"
      initialInterval="1m"
      initialPeriod="1d"
      ChartComponent={FakeChart}
      {...overrides}
    />,
  );
}

describe("ChartPanel", () => {
  it("opens the current URL in an independent chart window", async () => {
    window.history.replaceState({}, "", "/chart/instrument-aapl?interval=1m&period=1d&volume=1");
    const openWindow = vi.spyOn(window, "open").mockImplementation(() => null);
    renderPanel({
      createStream: createStreamHarness().factory,
      fetchHistory: vi.fn().mockResolvedValue(response()),
    });
    await screen.findByTestId("chart");

    fireEvent.click(screen.getByRole("button", { name: "Open chart window" }));

    expect(openWindow).toHaveBeenCalledWith(window.location.href, "_blank", "noopener,noreferrer");
    openWindow.mockRestore();
  });

  it("shows timestamp and OHLCV values for the inspected candle", async () => {
    renderPanel({
      ChartComponent: InspectableChart,
      createStream: createStreamHarness().factory,
      fetchHistory: vi.fn().mockResolvedValue(response()),
    });
    await screen.findByRole("button", { name: "Inspect candle" });

    fireEvent.click(screen.getByRole("button", { name: "Inspect candle" }));

    const inspection = screen.getByRole("status", { name: "Crosshair data" });
    expect(inspection).toHaveTextContent("Jul 24, 2026");
    expect(inspection).toHaveTextContent("Open 210.00");
    expect(inspection).toHaveTextContent("High 210.25");
    expect(inspection).toHaveTextContent("Low 209.95");
    expect(inspection).toHaveTextContent("Close 210.10");
    expect(inspection).toHaveTextContent("Volume 100");
  });

  it("shows loading, renders history, labels demo data, then starts streaming", async () => {
    const request = deferred<CandleHistoryResponse>();
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockReturnValue(request.promise);
    const stream = createStreamHarness();
    renderPanel({ createStream: stream.factory, fetchHistory });

    expect(screen.getByRole("status")).toHaveTextContent("Loading chart");
    expect(stream.factory).not.toHaveBeenCalled();

    await act(async () => {
      request.resolve(response());
      await request.promise;
    });

    expect(screen.getByTestId("chart")).toHaveTextContent('"close":"210.10"');
    expect(screen.getByText(/simulated demo data/i)).toBeVisible();
    expect(screen.getByRole("heading", { name: /AAPL.*1m.*1d/i })).toBeVisible();
    expect(screen.getByTestId("chart")).toHaveAccessibleName(
      "AAPL candlestick chart for 1d at 1m intervals. Latest close 210.10. Latest volume 100. Freshness FRESH.",
    );
    expect(fetchHistory).toHaveBeenCalledWith(
      "http://api.test",
      "instrument-aapl",
      "1m",
      "1d",
      expect.any(AbortSignal),
    );
    expect(stream.factory).toHaveBeenCalledTimes(1);
  });

  it("keeps interval and period independent while disabling invalid combinations", async () => {
    window.history.replaceState({}, "", "/chart/instrument-aapl?interval=1m&period=1d&volume=1");
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
    expect(new URLSearchParams(window.location.search).get("interval")).toBe("1h");
    expect(new URLSearchParams(window.location.search).get("period")).toBe("3mo");

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
    expect(chart).toHaveAccessibleName(/Latest close 210\.30/);
  });

  it("aborts requests and closes streams when parameters change or the panel unmounts", async () => {
    const signals: AbortSignal[] = [];
    const fetchHistory = vi.fn<NonNullable<ChartPanelProps["fetchHistory"]>>(
      (
        _baseUrl: string,
        _instrumentId: string,
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
          instrumentId="instrument-aapl"
          initialInterval="1m"
          initialPeriod="1d"
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

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not load this instrument's chart",
    );
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
    expect(screen.getByTestId("chart")).toHaveAccessibleName(/Freshness STALE/);
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

  it("shows volume by default and reports the latest volume in the chart label", async () => {
    renderPanel({
      createStream: createStreamHarness().factory,
      fetchHistory: vi.fn().mockResolvedValue(response()),
    });
    await screen.findByTestId("chart");

    expect(screen.getByRole("checkbox", { name: "Show volume" })).toBeChecked();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "true");
    expect(screen.getByTestId("chart")).toHaveAccessibleName(/Latest volume 100\./);
  });

  it("keeps the volume preference checked while history is still loading", async () => {
    const request = deferred<CandleHistoryResponse>();
    renderPanel({
      createStream: createStreamHarness().factory,
      fetchHistory: vi.fn().mockReturnValue(request.promise),
      initialShowVolume: true,
    });

    expect(screen.getByRole("status")).toHaveTextContent("Loading chart");
    expect(screen.getByRole("checkbox", { name: "Show volume" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Show volume" })).toBeEnabled();

    await act(async () => {
      request.resolve(response());
      await request.promise;
    });
    await screen.findByTestId("chart");
  });

  it("hides volume without refetching or losing candles when the toggle is cleared", async () => {
    window.history.replaceState({}, "", "/chart/instrument-aapl?interval=1m&period=1d&volume=1");
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockResolvedValue(response());
    renderPanel({ createStream: createStreamHarness().factory, fetchHistory });
    await screen.findByTestId("chart");
    expect(fetchHistory).toHaveBeenCalledTimes(1);

    const toggle = screen.getByRole("checkbox", { name: "Show volume" });
    fireEvent.click(toggle);

    expect(toggle).not.toBeChecked();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "false");
    expect(new URLSearchParams(window.location.search).get("volume")).toBe("0");
    expect(screen.getByTestId("chart")).toHaveTextContent('"close":"210.10"');
    expect(screen.getByTestId("chart")).toHaveAccessibleName(
      "AAPL candlestick chart for 1d at 1m intervals. Latest close 210.10. Freshness FRESH.",
    );
    expect(screen.getByRole("combobox", { name: "Candle interval" })).toHaveValue("1m");
    expect(screen.getByRole("combobox", { name: "Chart period" })).toHaveValue("1d");

    fireEvent.click(toggle);

    expect(toggle).toBeChecked();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "true");
    expect(new URLSearchParams(window.location.search).get("volume")).toBe("1");
    expect(fetchHistory).toHaveBeenCalledTimes(1);
  });

  it("honours an initial volume preference", async () => {
    renderPanel({
      createStream: createStreamHarness().factory,
      fetchHistory: vi.fn().mockResolvedValue(response()),
      initialShowVolume: false,
    });
    await screen.findByTestId("chart");

    expect(screen.getByRole("checkbox", { name: "Show volume" })).not.toBeChecked();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "false");
  });

  it("explains unavailable volume and disables the toggle without hiding prices", async () => {
    renderPanel({
      createStream: createStreamHarness().factory,
      fetchHistory: vi
        .fn()
        .mockResolvedValue(response({ candles: [{ ...firstCandle, volume: 0 }] })),
    });
    await screen.findByTestId("chart");

    expect(screen.getByText(/volume data is unavailable/i)).toBeVisible();
    const toggle = screen.getByRole("checkbox", { name: "Show volume" });
    expect(toggle).toBeChecked();
    expect(toggle).toBeDisabled();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "false");
    expect(screen.getByTestId("chart")).toHaveTextContent('"close":"210.10"');
    expect(screen.getByTestId("chart")).toHaveAccessibleName(
      "AAPL candlestick chart for 1d at 1m intervals. Latest close 210.10. Freshness FRESH.",
    );
  });

  it("toggles volume from the keyboard without refetching history", async () => {
    const fetchHistory: NonNullable<ChartPanelProps["fetchHistory"]> = vi
      .fn()
      .mockResolvedValue(response());
    renderPanel({ createStream: createStreamHarness().factory, fetchHistory });
    await screen.findByTestId("chart");

    const toggle = screen.getByRole("checkbox", { name: "Show volume" });
    toggle.focus();
    expect(toggle).toHaveFocus();

    fireEvent.keyDown(toggle, { key: " ", code: "Space" });
    fireEvent.click(toggle);

    expect(toggle).not.toBeChecked();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "false");

    fireEvent.keyDown(toggle, { key: "Enter", code: "Enter" });
    fireEvent.click(toggle);

    expect(toggle).toBeChecked();
    expect(screen.getByTestId("chart")).toHaveAttribute("data-show-volume", "true");
    expect(fetchHistory).toHaveBeenCalledTimes(1);
  });

  it("keeps the volume label in step with streamed updates", async () => {
    const stream = createStreamHarness();
    renderPanel({
      createStream: stream.factory,
      fetchHistory: vi.fn().mockResolvedValue(response()),
    });
    await screen.findByTestId("chart");

    act(() => {
      stream.connections[0]!.handlers.onUpdate(update({ close: "210.20", volume: 4200 }));
    });

    expect(screen.getByTestId("chart")).toHaveAccessibleName(/Latest volume 4,200\./);
  });
});
