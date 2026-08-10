"use client";

import { type ComponentType, useEffect, useRef, useState } from "react";

import { Empty } from "@/components/state/Empty";
import { ErrorState } from "@/components/state/ErrorState";
import { Loading } from "@/components/state/Loading";
import { CandlestickChart, type CandlestickChartProps } from "@/components/CandlestickChart";
import { createCandleStream, type CandleStream } from "@/lib/candleStream";
import { mergeCandleUpdate } from "@/lib/candleStore";
import { hasVolumeData } from "@/lib/chartSeries";
import {
  CANDLE_INTERVALS,
  CHART_PERIODS,
  fetchCandles,
  isCombinationSupported,
  supportedPeriodsForInterval,
  type CandleHistoryResponse,
  type CandleInterval,
  type ChartPeriod,
  type MarketCandle,
} from "@/lib/marketData";

type HistoryViewState = "loading" | "ready" | "empty" | "error";
type StreamViewState = "idle" | "connecting" | "connected" | "disconnected" | "error";

export type ChartPanelProps = {
  apiBaseUrl: string;
  instrumentId: string;
  initialInterval?: CandleInterval;
  initialPeriod?: ChartPeriod;
  initialShowVolume?: boolean;
  fetchHistory?: typeof fetchCandles;
  createStream?: typeof createCandleStream;
  ChartComponent?: ComponentType<CandlestickChartProps>;
};

const INTERVAL_LABELS: Record<CandleInterval, string> = {
  "1m": "1 minute",
  "2m": "2 minutes",
  "5m": "5 minutes",
  "15m": "15 minutes",
  "30m": "30 minutes",
  "1h": "1 hour",
  "1d": "1 day",
};

const VOLUME_FORMAT = new Intl.NumberFormat("en-US");

const PERIOD_LABELS: Record<ChartPeriod, string> = {
  "1d": "1 day",
  "5d": "5 days",
  "1mo": "1 month",
  "3mo": "3 months",
  "6mo": "6 months",
  "1y": "1 year",
};

export function ChartPanel({
  apiBaseUrl,
  instrumentId,
  initialInterval = "1d",
  initialPeriod = "1y",
  initialShowVolume = true,
  fetchHistory = fetchCandles,
  createStream = createCandleStream,
  ChartComponent = CandlestickChart,
}: ChartPanelProps) {
  const [interval, setInterval] = useState<CandleInterval>(initialInterval);
  const [period, setPeriod] = useState<ChartPeriod>(
    isCombinationSupported(initialInterval, initialPeriod)
      ? initialPeriod
      : (supportedPeriodsForInterval(initialInterval)[0] ?? initialPeriod),
  );
  const [showVolume, setShowVolume] = useState(initialShowVolume);
  const [retrySequence, setRetrySequence] = useState(0);
  const [historyState, setHistoryState] = useState<HistoryViewState>("loading");
  const [streamState, setStreamState] = useState<StreamViewState>("idle");
  const [candles, setCandles] = useState<readonly MarketCandle[]>([]);
  const [history, setHistory] = useState<CandleHistoryResponse | null>(null);
  const requestSequence = useRef(0);
  const lastStreamSequence = useRef(0);
  const activeStream = useRef<CandleStream | null>(null);

  useEffect(() => {
    const requestId = ++requestSequence.current;
    const controller = new AbortController();
    let connection: CandleStream | null = null;

    activeStream.current?.close();
    activeStream.current = null;
    lastStreamSequence.current = 0;
    setHistoryState("loading");
    setStreamState("idle");
    setCandles([]);
    setHistory(null);

    void fetchHistory(apiBaseUrl, instrumentId, interval, period, controller.signal)
      .then((response) => {
        if (controller.signal.aborted || requestSequence.current !== requestId) {
          return;
        }

        setHistory(response);
        if (response.metadata.state === "EMPTY" || response.candles.length === 0) {
          setHistoryState("empty");
          return;
        }

        setCandles(response.candles);
        setHistoryState("ready");
        setStreamState("connecting");
        connection = createStream(apiBaseUrl, response.symbol, interval, {
          onOpen: () => {
            if (requestSequence.current !== requestId) {
              return;
            }
            lastStreamSequence.current = 0;
            setStreamState("connected");
          },
          onUpdate: (update) => {
            if (requestSequence.current !== requestId) {
              return;
            }
            setCandles((currentCandles) => {
              const result = mergeCandleUpdate(currentCandles, update, lastStreamSequence.current);
              lastStreamSequence.current = result.lastSequence;
              return result.candles;
            });
          },
          onDisconnected: () => {
            if (requestSequence.current !== requestId) {
              return;
            }
            lastStreamSequence.current = 0;
            setStreamState("disconnected");
          },
          onError: () => {
            if (requestSequence.current === requestId) {
              setStreamState("error");
            }
          },
        });
        activeStream.current = connection;
      })
      .catch((error: unknown) => {
        if (
          controller.signal.aborted ||
          requestSequence.current !== requestId ||
          (error instanceof DOMException && error.name === "AbortError")
        ) {
          return;
        }
        setHistoryState("error");
      });

    return () => {
      controller.abort();
      connection?.close();
      if (activeStream.current === connection) {
        activeStream.current = null;
      }
      if (requestSequence.current === requestId) {
        requestSequence.current += 1;
      }
    };
  }, [apiBaseUrl, createStream, fetchHistory, instrumentId, interval, period, retrySequence]);

  function changeInterval(nextInterval: CandleInterval) {
    setInterval(nextInterval);
    if (!isCombinationSupported(nextInterval, period)) {
      setPeriod(supportedPeriodsForInterval(nextInterval)[0] ?? period);
    }
  }

  function changeVolumeVisibility(nextShowVolume: boolean) {
    setShowVolume(nextShowVolume);
    const url = new URL(window.location.href);
    url.searchParams.set("volume", nextShowVolume ? "1" : "0");
    window.history.replaceState(window.history.state, "", url);
  }

  const freshnessState = history?.metadata.freshness?.state;
  const isStale = freshnessState === "STALE" || freshnessState === "DELAYED";
  const displaySymbol = history?.symbol;
  const latestClose = candles.at(-1)?.close;
  const volumeAvailable = hasVolumeData(candles);
  const volumeVisible = showVolume && volumeAvailable;
  const latestVolume = candles.at(-1)?.volume;
  const volumeLabel =
    volumeVisible && latestVolume !== undefined
      ? ` Latest volume ${VOLUME_FORMAT.format(latestVolume)}.`
      : "";

  return (
    <section className="chart-panel" aria-labelledby="chart-panel-title">
      <div className="chart-panel-heading">
        <div>
          <h2 id="chart-panel-title">
            {displaySymbol ? `${displaySymbol} candlestick chart` : "Candlestick chart"} ·{" "}
            {interval} · {period}
          </h2>
          <p>Historical OHLCV candles with continuously updating demo prices.</p>
        </div>
        <div className="chart-controls">
          <label>
            Candle interval
            <select
              value={interval}
              onChange={(event) => changeInterval(event.target.value as CandleInterval)}
            >
              {CANDLE_INTERVALS.map((option) => (
                <option key={option} value={option}>
                  {INTERVAL_LABELS[option]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Chart period
            <select
              value={period}
              onChange={(event) => setPeriod(event.target.value as ChartPeriod)}
            >
              {CHART_PERIODS.map((option) => (
                <option
                  key={option}
                  value={option}
                  disabled={!isCombinationSupported(interval, option)}
                >
                  {PERIOD_LABELS[option]}
                </option>
              ))}
            </select>
          </label>
          <label className="chart-toggle">
            <input
              type="checkbox"
              checked={showVolume}
              disabled={historyState === "ready" && !volumeAvailable}
              onChange={(event) => changeVolumeVisibility(event.target.checked)}
            />
            Show volume
          </label>
        </div>
      </div>

      {historyState === "loading" ? <Loading message="Loading chart…" /> : null}
      {historyState === "empty" ? (
        <Empty
          message={`No candle data is available for ${displaySymbol ?? "this instrument"} at this timeframe.`}
        />
      ) : null}
      {historyState === "error" ? (
        <div className="chart-message">
          <ErrorState message="Could not load this instrument's chart. Try again." />
          <button type="button" onClick={() => setRetrySequence((value) => value + 1)}>
            Retry chart
          </button>
        </div>
      ) : null}

      {historyState === "ready" ? (
        <>
          <div className="chart-statuses" aria-live="polite">
            {history?.dataSource === "demo" ? (
              <span className="chart-badge">Simulated demo data — not live exchange data</span>
            ) : null}
            {isStale ? (
              <span className="chart-badge chart-badge-warning">
                Market data is {freshnessState === "DELAYED" ? "delayed" : "stale"}.
              </span>
            ) : null}
            {streamState === "disconnected" ? (
              <span className="chart-badge chart-badge-warning">
                Live updates disconnected; reconnecting…
              </span>
            ) : null}
            {volumeAvailable ? null : (
              <span className="chart-badge chart-badge-warning">
                Volume data is unavailable for this timeframe.
              </span>
            )}
          </div>
          {streamState === "error" ? (
            <div className="chart-message">
              <ErrorState message="Live chart updates stopped. Retry to reconnect." />
              <button type="button" onClick={() => setRetrySequence((value) => value + 1)}>
                Retry chart
              </button>
            </div>
          ) : null}
          <ChartComponent
            candles={candles}
            showVolume={volumeVisible}
            accessibleLabel={`${displaySymbol ?? "Instrument"} candlestick chart for ${period} at ${interval} intervals. Latest close ${latestClose ?? "unavailable"}.${volumeLabel} Freshness ${freshnessState ?? "UNKNOWN"}.`}
            className="candlestick-chart"
          />
        </>
      ) : null}
    </section>
  );
}
