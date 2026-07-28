import { describe, expect, it } from "vitest";

import { mergeCandleUpdate } from "./candleStore";
import type { MarketCandle, StreamCandleUpdate } from "./marketData";

const firstCandle: MarketCandle = {
  timestamp: "2026-07-24T15:30:00Z",
  open: "210.0100",
  high: "210.2500",
  low: "209.9900",
  close: "210.1250",
  volume: 1234,
};

function update(overrides: Partial<StreamCandleUpdate> = {}): StreamCandleUpdate {
  return {
    ...firstCandle,
    symbol: "AAPL",
    interval: "1m",
    eventTimestamp: "2026-07-24T15:30:06Z",
    sequence: 2,
    ...overrides,
  };
}

describe("mergeCandleUpdate", () => {
  it("replaces the active candle without mutating input or decimal strings", () => {
    const input = [firstCandle];
    const result = mergeCandleUpdate(
      input,
      update({
        high: "210.3750",
        close: "210.3333",
        volume: 1300,
      }),
      1,
    );

    expect(result.changed).toBe(true);
    expect(result.lastSequence).toBe(2);
    expect(result.candles).toEqual([
      {
        ...firstCandle,
        high: "210.3750",
        close: "210.3333",
        volume: 1300,
      },
    ]);
    expect(result.candles[0]?.close).toBe("210.3333");
    expect(input).toEqual([firstCandle]);
    expect(result.candles).not.toBe(input);
  });

  it("appends a newer candle without filling missing buckets", () => {
    const next = update({
      timestamp: "2026-07-24T15:33:00Z",
      open: "211.00",
      high: "211.00",
      low: "211.00",
      close: "211.00",
      sequence: 3,
    });

    const result = mergeCandleUpdate([firstCandle], next, 2);

    expect(result.changed).toBe(true);
    expect(result.lastSequence).toBe(3);
    expect(result.candles).toHaveLength(2);
    expect(result.candles[1]?.timestamp).toBe("2026-07-24T15:33:00Z");
  });

  it.each([
    ["duplicate", 2],
    ["older", 1],
  ])("ignores %s sequence updates", (_label, sequence) => {
    const input = [firstCandle];

    const result = mergeCandleUpdate(input, update({ sequence }), 2);

    expect(result).toEqual({
      candles: input,
      lastSequence: 2,
      changed: false,
    });
    expect(result.candles).toBe(input);
  });

  it("ignores a candle older than the latest timestamp", () => {
    const input = [firstCandle];

    const result = mergeCandleUpdate(
      input,
      update({
        timestamp: "2026-07-24T15:29:00Z",
        sequence: 3,
      }),
      2,
    );

    expect(result).toEqual({
      candles: input,
      lastSequence: 2,
      changed: false,
    });
  });

  it("appends the first update to an empty store", () => {
    const result = mergeCandleUpdate([], update({ sequence: 1 }), 0);

    expect(result.changed).toBe(true);
    expect(result.lastSequence).toBe(1);
    expect(result.candles).toHaveLength(1);
  });
});
