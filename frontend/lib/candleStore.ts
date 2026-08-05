import type { MarketCandle, StreamCandleUpdate } from "./marketData";

export type CandleMergeResult = {
  candles: readonly MarketCandle[];
  lastSequence: number;
  changed: boolean;
};

export function mergeCandleUpdate(
  candles: readonly MarketCandle[],
  update: StreamCandleUpdate,
  lastSequence: number,
): CandleMergeResult {
  if (update.sequence <= lastSequence) {
    return { candles, lastSequence, changed: false };
  }

  const latest = candles.at(-1);
  if (latest && update.timestamp < latest.timestamp) {
    return { candles, lastSequence, changed: false };
  }

  const nextCandle = toMarketCandle(update);
  if (latest?.timestamp === update.timestamp) {
    return {
      candles: [...candles.slice(0, -1), nextCandle],
      lastSequence: update.sequence,
      changed: true,
    };
  }

  return {
    candles: [...candles, nextCandle],
    lastSequence: update.sequence,
    changed: true,
  };
}

function toMarketCandle(update: StreamCandleUpdate): MarketCandle {
  return {
    timestamp: update.timestamp,
    open: update.open,
    high: update.high,
    low: update.low,
    close: update.close,
    volume: update.volume,
  };
}
