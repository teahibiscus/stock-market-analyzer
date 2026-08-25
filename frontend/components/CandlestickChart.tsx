"use client";

import { type KeyboardEvent, useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  createChart,
  type ISeriesApi,
} from "lightweight-charts";

import { seriesChanged, toPriceSeries, toVolumeSeries } from "@/lib/chartSeries";
import type { MarketCandle } from "@/lib/marketData";

export type CandlestickChartProps = {
  candles: readonly MarketCandle[];
  accessibleLabel: string;
  showVolume?: boolean;
  className?: string;
  onInspectionChange?: (candle: MarketCandle | null) => void;
};

const PRICE_MARGINS_WITH_VOLUME = { top: 0.1, bottom: 0.3 };
const PRICE_MARGINS_WITHOUT_VOLUME = { top: 0.1, bottom: 0.1 };

export function CandlestickChart({
  candles,
  accessibleLabel,
  showVolume = true,
  className,
  onInspectionChange,
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const priceSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const previousCandlesRef = useRef<readonly MarketCandle[]>([]);
  const candlesRef = useRef(candles);
  const inspectionCallbackRef = useRef(onInspectionChange);
  const keyboardIndexRef = useRef(-1);

  candlesRef.current = candles;
  inspectionCallbackRef.current = onInspectionChange;

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }

    const chart = createChart(container, {
      width: Math.max(container.clientWidth, 300),
      height: container.clientHeight || 400,
      layout: {
        background: { type: ColorType.Solid, color: "#0f172a" },
        textColor: "#cbd5e1",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      rightPriceScale: { borderColor: "#334155" },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
        secondsVisible: false,
      },
    });
    priceSeriesRef.current = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    // An empty price scale id keeps volume as an overlay pinned to the lower band
    // of the same pane rather than competing with the price scale.
    volumeSeriesRef.current = chart.addSeries(HistogramSeries, {
      priceScaleId: "",
      priceFormat: { type: "volume" },
      priceLineVisible: false,
      lastValueVisible: false,
    });
    volumeSeriesRef.current.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    const handleCrosshairMove = (parameter: { time?: unknown }) => {
      const timestamp =
        typeof parameter.time === "number"
          ? parameter.time
          : parameter.time !== null && typeof parameter.time === "object"
            ? Date.UTC(
                (parameter.time as { year: number }).year,
                (parameter.time as { month: number }).month - 1,
                (parameter.time as { day: number }).day,
              ) / 1_000
            : null;
      const inspected =
        timestamp === null
          ? null
          : (candlesRef.current.find(
              (candle) => Date.parse(candle.timestamp) / 1_000 === timestamp,
            ) ?? null);
      inspectionCallbackRef.current?.(inspected);
    };
    chart.subscribeCrosshairMove(handleCrosshairMove);

    const resize = () => {
      chart.applyOptions({
        width: Math.max(container.clientWidth, 300),
        height: container.clientHeight || 400,
      });
    };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resize);
    observer?.observe(container);

    return () => {
      observer?.disconnect();
      priceSeriesRef.current = null;
      volumeSeriesRef.current = null;
      previousCandlesRef.current = [];
      chart.unsubscribeCrosshairMove(handleCrosshairMove);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    const volumeSeries = volumeSeriesRef.current;
    const priceSeries = priceSeriesRef.current;
    if (volumeSeries === null || priceSeries === null) {
      return;
    }

    volumeSeries.applyOptions({ visible: showVolume });
    priceSeries.priceScale().applyOptions({
      scaleMargins: showVolume ? PRICE_MARGINS_WITH_VOLUME : PRICE_MARGINS_WITHOUT_VOLUME,
    });
  }, [showVolume]);

  useEffect(() => {
    const priceSeries = priceSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    if (priceSeries === null || volumeSeries === null) {
      return;
    }

    const change = seriesChanged(previousCandlesRef.current, candles);
    if (change === "none") {
      return;
    }

    if (change === "reset") {
      priceSeries.setData(toPriceSeries(candles));
      volumeSeries.setData(toVolumeSeries(candles));
    } else {
      priceSeries.update(toPriceSeries(candles).at(-1)!);
      volumeSeries.update(toVolumeSeries(candles).at(-1)!);
    }

    previousCandlesRef.current = candles;
  }, [candles]);

  function inspectWithKeyboard(event: KeyboardEvent<HTMLDivElement>) {
    if (candles.length === 0 || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      return;
    }

    event.preventDefault();
    if (event.key === "Home") {
      keyboardIndexRef.current = 0;
    } else if (event.key === "End") {
      keyboardIndexRef.current = candles.length - 1;
    } else if (event.key === "ArrowLeft") {
      keyboardIndexRef.current =
        keyboardIndexRef.current < 0
          ? candles.length - 1
          : Math.max(0, keyboardIndexRef.current - 1);
    } else {
      keyboardIndexRef.current =
        keyboardIndexRef.current < 0
          ? 0
          : Math.min(candles.length - 1, keyboardIndexRef.current + 1);
    }
    inspectionCallbackRef.current?.(candles[keyboardIndexRef.current] ?? null);
  }

  return (
    <div
      ref={containerRef}
      className={className}
      role="img"
      aria-label={accessibleLabel}
      tabIndex={0}
      onKeyDown={inspectWithKeyboard}
    />
  );
}
