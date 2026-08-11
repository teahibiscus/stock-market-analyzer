import { describe, expect, it } from "vitest";

import {
  VOLUME_DOWN_COLOR,
  VOLUME_UP_COLOR,
  hasVolumeData,
  seriesChanged,
  toPriceSeries,
  toVolumeSeries,
} from "@/lib/chartSeries";
import type { MarketCandle } from "@/lib/marketData";

function candle(overrides: Partial<MarketCandle> = {}): MarketCandle {
  return {
    timestamp: "2026-01-02T00:00:00Z",
    open: "100.00",
    high: "105.00",
    low: "99.00",
    close: "104.00",
    volume: 1_000,
    ...overrides,
  };
}

describe("toPriceSeries", () => {
  it("maps candles to numeric OHLC points keyed by unix seconds", () => {
    const series = toPriceSeries([candle()]);

    expect(series).toEqual([
      {
        time: Date.parse("2026-01-02T00:00:00Z") / 1_000,
        open: 100,
        high: 105,
        low: 99,
        close: 104,
      },
    ]);
  });

  it("preserves candle order", () => {
    const series = toPriceSeries([
      candle({ timestamp: "2026-01-02T00:00:00Z" }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
    ]);

    expect(series.map((point) => point.time)).toEqual([
      Date.parse("2026-01-02T00:00:00Z") / 1_000,
      Date.parse("2026-01-03T00:00:00Z") / 1_000,
    ]);
  });

  it("returns an empty series for no candles", () => {
    expect(toPriceSeries([])).toEqual([]);
  });
});

describe("toVolumeSeries", () => {
  it("maps volume to histogram values keyed by unix seconds", () => {
    const series = toVolumeSeries([candle({ volume: 4_200 })]);

    expect(series).toEqual([
      {
        time: Date.parse("2026-01-02T00:00:00Z") / 1_000,
        value: 4_200,
        color: VOLUME_UP_COLOR,
      },
    ]);
  });

  it("colours a rising candle with the up colour", () => {
    const [point] = toVolumeSeries([candle({ open: "100.00", close: "104.00" })]);

    expect(point?.color).toBe(VOLUME_UP_COLOR);
  });

  it("colours a falling candle with the down colour", () => {
    const [point] = toVolumeSeries([candle({ open: "104.00", close: "100.00" })]);

    expect(point?.color).toBe(VOLUME_DOWN_COLOR);
  });

  it("treats an unchanged candle as rising", () => {
    const [point] = toVolumeSeries([candle({ open: "100.00", close: "100.00" })]);

    expect(point?.color).toBe(VOLUME_UP_COLOR);
  });

  it("coerces a missing volume to zero rather than NaN", () => {
    const [point] = toVolumeSeries([candle({ volume: undefined as unknown as number })]);

    expect(point?.value).toBe(0);
  });
});

describe("hasVolumeData", () => {
  it("is false for no candles", () => {
    expect(hasVolumeData([])).toBe(false);
  });

  it("is false when every volume is zero", () => {
    expect(hasVolumeData([candle({ volume: 0 }), candle({ volume: 0 })])).toBe(false);
  });

  it("is false when every volume is missing", () => {
    expect(hasVolumeData([candle({ volume: undefined as unknown as number })])).toBe(false);
  });

  it("is true when at least one candle reports volume", () => {
    expect(hasVolumeData([candle({ volume: 0 }), candle({ volume: 12 })])).toBe(true);
  });
});

describe("seriesChanged", () => {
  it("reports no change for identical candles", () => {
    const candles = [candle()];

    expect(seriesChanged(candles, [candle()])).toBe("none");
  });

  it("reports a reset when the first data arrives", () => {
    expect(seriesChanged([], [candle()])).toBe("reset");
  });

  it("reports a reset when the candles are cleared", () => {
    expect(seriesChanged([candle()], [])).toBe("reset");
  });

  it("reports an update when only the last candle changes", () => {
    const previous = [candle({ timestamp: "2026-01-02T00:00:00Z" })];
    const next = [candle({ timestamp: "2026-01-02T00:00:00Z", close: "106.00" })];

    expect(seriesChanged(previous, next)).toBe("update-last");
  });

  it("reports an update when only the last candle's volume changes", () => {
    const previous = [candle({ volume: 1_000 })];
    const next = [candle({ volume: 1_500 })];

    expect(seriesChanged(previous, next)).toBe("update-last");
  });

  it("reports an append when one newer candle is added", () => {
    const previous = [candle({ timestamp: "2026-01-02T00:00:00Z" })];
    const next = [
      candle({ timestamp: "2026-01-02T00:00:00Z" }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
    ];

    expect(seriesChanged(previous, next)).toBe("append");
  });

  it("reports a reset when an earlier candle changes", () => {
    const previous = [
      candle({ timestamp: "2026-01-02T00:00:00Z", close: "104.00" }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
    ];
    const next = [
      candle({ timestamp: "2026-01-02T00:00:00Z", close: "101.00" }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
    ];

    expect(seriesChanged(previous, next)).toBe("reset");
  });

  it("reports a reset when an earlier candle's volume changes", () => {
    const previous = [
      candle({ timestamp: "2026-01-02T00:00:00Z", volume: 1_000 }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
    ];
    const next = [
      candle({ timestamp: "2026-01-02T00:00:00Z", volume: 2_000 }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
    ];

    expect(seriesChanged(previous, next)).toBe("reset");
  });

  it("reports a reset when the appended candle is not newer", () => {
    const previous = [candle({ timestamp: "2026-01-03T00:00:00Z" })];
    const next = [
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
      candle({ timestamp: "2026-01-02T00:00:00Z" }),
    ];

    expect(seriesChanged(previous, next)).toBe("reset");
  });

  it("reports a reset when more than one candle is added", () => {
    const previous = [candle({ timestamp: "2026-01-02T00:00:00Z" })];
    const next = [
      candle({ timestamp: "2026-01-02T00:00:00Z" }),
      candle({ timestamp: "2026-01-03T00:00:00Z" }),
      candle({ timestamp: "2026-01-04T00:00:00Z" }),
    ];

    expect(seriesChanged(previous, next)).toBe("reset");
  });
});
