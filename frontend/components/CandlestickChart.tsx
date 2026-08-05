"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type CandlestickData,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { MarketCandle } from "@/lib/marketData";

export type CandlestickChartProps = {
  candles: readonly MarketCandle[];
  accessibleLabel: string;
  className?: string;
};

type ChartCandle = CandlestickData<UTCTimestamp>;

export function CandlestickChart({ candles, accessibleLabel, className }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const previousDataRef = useRef<ChartCandle[]>([]);

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
    seriesRef.current = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

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
      seriesRef.current = null;
      previousDataRef.current = [];
      chart.remove();
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (series === null) {
      return;
    }

    const nextData = candles.map(toChartCandle);
    const previousData = previousDataRef.current;
    if (canUpdateLast(previousData, nextData)) {
      series.update(nextData.at(-1)!);
    } else if (canAppend(previousData, nextData)) {
      series.update(nextData.at(-1)!);
    } else {
      series.setData(nextData);
    }
    previousDataRef.current = nextData;
  }, [candles]);

  return <div ref={containerRef} className={className} role="img" aria-label={accessibleLabel} />;
}

function toChartCandle(candle: MarketCandle): ChartCandle {
  return {
    time: Math.floor(Date.parse(candle.timestamp) / 1_000) as UTCTimestamp,
    open: Number(candle.open),
    high: Number(candle.high),
    low: Number(candle.low),
    close: Number(candle.close),
  };
}

function canUpdateLast(previous: ChartCandle[], next: ChartCandle[]): boolean {
  return (
    previous.length > 0 &&
    previous.length === next.length &&
    previous.at(-1)?.time === next.at(-1)?.time &&
    equalCandles(previous.slice(0, -1), next.slice(0, -1))
  );
}

function canAppend(previous: ChartCandle[], next: ChartCandle[]): boolean {
  return (
    previous.length > 0 &&
    next.length === previous.length + 1 &&
    equalCandles(previous, next.slice(0, -1)) &&
    Number(next.at(-1)?.time) > Number(previous.at(-1)?.time)
  );
}

function equalCandles(left: ChartCandle[], right: ChartCandle[]): boolean {
  return left.every(
    (candle, index) =>
      candle.time === right[index]?.time &&
      candle.open === right[index]?.open &&
      candle.high === right[index]?.high &&
      candle.low === right[index]?.low &&
      candle.close === right[index]?.close,
  );
}
