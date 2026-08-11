import type { CandlestickData, HistogramData, UTCTimestamp } from "lightweight-charts";

import type { MarketCandle } from "./marketData";

export type PricePoint = CandlestickData<UTCTimestamp>;
export type VolumePoint = HistogramData<UTCTimestamp>;

/** How the rendered series must be reconciled with the next set of candles. */
export type SeriesChange = "none" | "update-last" | "append" | "reset";

export const VOLUME_UP_COLOR = "rgba(34, 197, 94, 0.5)";
export const VOLUME_DOWN_COLOR = "rgba(239, 68, 68, 0.5)";

export function toPriceSeries(candles: readonly MarketCandle[]): PricePoint[] {
  return candles.map((candle) => ({
    time: toChartTime(candle.timestamp),
    open: Number(candle.open),
    high: Number(candle.high),
    low: Number(candle.low),
    close: Number(candle.close),
  }));
}

export function toVolumeSeries(candles: readonly MarketCandle[]): VolumePoint[] {
  return candles.map((candle) => ({
    time: toChartTime(candle.timestamp),
    value: toVolume(candle.volume),
    color: Number(candle.close) < Number(candle.open) ? VOLUME_DOWN_COLOR : VOLUME_UP_COLOR,
  }));
}

export function hasVolumeData(candles: readonly MarketCandle[]): boolean {
  return candles.some((candle) => toVolume(candle.volume) > 0);
}

export function seriesChanged(
  previous: readonly MarketCandle[],
  next: readonly MarketCandle[],
): SeriesChange {
  if (previous.length === 0 || next.length === 0) {
    return previous.length === next.length ? "none" : "reset";
  }

  if (previous.length === next.length) {
    if (!samePrefix(previous, next, previous.length - 1)) {
      return "reset";
    }
    const previousLast = previous.at(-1)!;
    const nextLast = next.at(-1)!;
    if (previousLast.timestamp !== nextLast.timestamp) {
      return "reset";
    }
    return sameCandle(previousLast, nextLast) ? "none" : "update-last";
  }

  if (next.length === previous.length + 1 && samePrefix(previous, next, previous.length)) {
    const appended = next.at(-1)!;
    return toChartTime(appended.timestamp) > toChartTime(previous.at(-1)!.timestamp)
      ? "append"
      : "reset";
  }

  return "reset";
}

function toChartTime(timestamp: string): UTCTimestamp {
  return Math.floor(Date.parse(timestamp) / 1_000) as UTCTimestamp;
}

function toVolume(volume: number): number {
  return Number.isFinite(volume) ? Number(volume) : 0;
}

function samePrefix(
  previous: readonly MarketCandle[],
  next: readonly MarketCandle[],
  length: number,
): boolean {
  for (let index = 0; index < length; index += 1) {
    if (!sameCandle(previous[index]!, next[index]!)) {
      return false;
    }
  }
  return true;
}

function sameCandle(left: MarketCandle, right: MarketCandle): boolean {
  return (
    left.timestamp === right.timestamp &&
    left.open === right.open &&
    left.high === right.high &&
    left.low === right.low &&
    left.close === right.close &&
    toVolume(left.volume) === toVolume(right.volume)
  );
}
