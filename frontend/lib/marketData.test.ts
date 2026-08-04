import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError } from "./apiClient";
import {
  CANDLE_INTERVALS,
  CHART_PERIODS,
  fetchCandles,
  isCombinationSupported,
  supportedPeriodsForInterval,
  type CandleHistoryResponse,
} from "./marketData";

const historyResponse: CandleHistoryResponse = {
  symbol: "AAPL",
  interval: "1m",
  period: "1d",
  timezone: "UTC",
  dataSource: "demo",
  asOf: "2026-07-24T15:30:05Z",
  candles: [
    {
      timestamp: "2026-07-24T15:30:00Z",
      open: "210.0100",
      high: "210.2500",
      low: "209.9900",
      close: "210.1250",
      volume: 1234,
    },
  ],
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
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("market-data compatibility", () => {
  it("exposes the complete canonical interval and period options", () => {
    expect(CANDLE_INTERVALS).toEqual(["1m", "2m", "5m", "15m", "30m", "1h", "1d"]);
    expect(CHART_PERIODS).toEqual(["1d", "5d", "1mo", "3mo", "6mo", "1y"]);
  });

  it("mirrors the backend compatibility matrix", () => {
    expect(supportedPeriodsForInterval("1m")).toEqual(["1d", "5d"]);
    expect(supportedPeriodsForInterval("2m")).toEqual(["1d", "5d"]);
    expect(supportedPeriodsForInterval("5m")).toEqual(["1d", "5d", "1mo"]);
    expect(supportedPeriodsForInterval("15m")).toEqual(["1d", "5d", "1mo"]);
    expect(supportedPeriodsForInterval("30m")).toEqual(["1d", "5d", "1mo"]);
    expect(supportedPeriodsForInterval("1h")).toEqual(["1d", "5d", "1mo", "3mo", "6mo"]);
    expect(supportedPeriodsForInterval("1d")).toEqual(["1mo", "3mo", "6mo", "1y"]);
    expect(isCombinationSupported("1m", "1d")).toBe(true);
    expect(isCombinationSupported("1m", "1mo")).toBe(false);
  });
});

describe("fetchCandles", () => {
  it("uses the instrument ID, constructs canonical parameters, and forwards the abort signal", async () => {
    const signal = new AbortController().signal;
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(historyResponse),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      fetchCandles("http://127.0.0.1:8000/", "instrument/aapl", "1m", "1d", signal),
    ).resolves.toBe(historyResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/charts/instrument%2Faapl?interval=1m&period=1d",
      {
        headers: { Accept: "application/json" },
        signal,
      },
    );
  });

  it("rejects unsupported combinations without issuing a request", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const error = await fetchCandles(
      "http://127.0.0.1:8000",
      "AAPL",
      "1m",
      "1mo",
      new AbortController().signal,
    ).catch((reason: unknown) => reason);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "VALIDATION_ERROR",
      recoverable: true,
      status: 422,
    });
  });

  it("converts RFC 9457 responses into ApiClientError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: () =>
          Promise.resolve({
            code: "DEPENDENCY_ERROR",
            detail: "Market data is temporarily unavailable.",
            correlationId: "candles-correlation",
            recoverable: true,
          }),
      }),
    );

    const error = await fetchCandles(
      "http://127.0.0.1:8000",
      "AAPL",
      "1d",
      "1mo",
      new AbortController().signal,
    ).catch((reason: unknown) => reason);

    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "DEPENDENCY_ERROR",
      correlationId: "candles-correlation",
      message: "Market data is temporarily unavailable.",
      recoverable: true,
      status: 503,
    });
  });

  it("uses a transport-safe fallback for non-JSON failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: () => Promise.reject(new SyntaxError("invalid JSON")),
      }),
    );

    await expect(
      fetchCandles("http://127.0.0.1:8000", "AAPL", "1d", "1mo", new AbortController().signal),
    ).rejects.toMatchObject({
      code: "DEPENDENCY_ERROR",
      message: "Candle history request failed with status 502",
      status: 502,
    });
  });
});
