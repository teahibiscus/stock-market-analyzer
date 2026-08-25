import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MarketCandle } from "@/lib/marketData";

const priceUpdate = vi.fn();
const priceSetData = vi.fn();
const priceApplyOptions = vi.fn();
const priceScaleApplyOptions = vi.fn();
const volumeUpdate = vi.fn();
const volumeSetData = vi.fn();
const volumeApplyOptions = vi.fn();
const volumeScaleApplyOptions = vi.fn();
const chartApplyOptions = vi.fn();
const chartRemove = vi.fn();
const addSeries = vi.fn();
const subscribeCrosshairMove = vi.fn();
const unsubscribeCrosshairMove = vi.fn();

vi.mock("lightweight-charts", () => {
  const CandlestickSeries = { type: "Candlestick" };
  const HistogramSeries = { type: "Histogram" };
  return {
    CandlestickSeries,
    HistogramSeries,
    ColorType: { Solid: "solid" },
    createChart: vi.fn(() => ({
      addSeries,
      applyOptions: chartApplyOptions,
      remove: chartRemove,
      subscribeCrosshairMove,
      unsubscribeCrosshairMove,
      priceScale: vi.fn(() => ({ applyOptions: priceScaleApplyOptions })),
    })),
  };
});

import { CandlestickChart } from "./CandlestickChart";
import { CandlestickSeries, HistogramSeries, createChart } from "lightweight-charts";

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

describe("CandlestickChart", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    addSeries.mockImplementation((definition) => {
      if (definition === CandlestickSeries) {
        return {
          update: priceUpdate,
          setData: priceSetData,
          applyOptions: priceApplyOptions,
          priceScale: () => ({ applyOptions: priceScaleApplyOptions }),
        };
      }
      return {
        update: volumeUpdate,
        setData: volumeSetData,
        applyOptions: volumeApplyOptions,
        priceScale: () => ({ applyOptions: volumeScaleApplyOptions }),
      };
    });
  });

  it("reports the candle under the crosshair for data inspection", () => {
    const onInspectionChange = vi.fn();
    render(
      <CandlestickChart
        candles={[candle()]}
        accessibleLabel="AAPL chart"
        onInspectionChange={onInspectionChange}
      />,
    );

    const handler = subscribeCrosshairMove.mock.calls[0]?.[0] as
      ((parameter: { time: number }) => void) | undefined;
    expect(handler).toBeDefined();
    act(() => handler?.({ time: Date.parse("2026-01-02T00:00:00Z") / 1_000 }));

    expect(onInspectionChange).toHaveBeenCalledWith(candle());
  });

  it("supports keyboard candle inspection", () => {
    const onInspectionChange = vi.fn();
    render(
      <CandlestickChart
        candles={[candle()]}
        accessibleLabel="AAPL chart"
        onInspectionChange={onInspectionChange}
      />,
    );

    const chart = screen.getByRole("img", { name: "AAPL chart" });
    expect(chart).toHaveAttribute("tabindex", "0");
    fireEvent.keyDown(chart, { key: "ArrowLeft" });

    expect(onInspectionChange).toHaveBeenCalledWith(candle());
  });

  it("creates an overlay histogram series for volume", () => {
    render(
      <CandlestickChart
        candles={[candle()]}
        accessibleLabel="AAPL chart"
        showVolume
        className="candlestick-chart"
      />,
    );

    expect(createChart).toHaveBeenCalledOnce();
    expect(addSeries).toHaveBeenCalledWith(CandlestickSeries, expect.any(Object));
    expect(addSeries).toHaveBeenCalledWith(
      HistogramSeries,
      expect.objectContaining({
        priceScaleId: "",
        priceFormat: { type: "volume" },
      }),
    );
    expect(volumeScaleApplyOptions).toHaveBeenCalledWith({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    expect(volumeSetData).toHaveBeenCalledWith([
      expect.objectContaining({
        time: Date.parse("2026-01-02T00:00:00Z") / 1_000,
        value: 1_000,
      }),
    ]);
  });

  it("toggles histogram visibility from the showVolume prop", () => {
    const view = render(
      <CandlestickChart candles={[candle()]} accessibleLabel="AAPL chart" showVolume />,
    );

    expect(volumeApplyOptions).toHaveBeenCalledWith({ visible: true });

    view.rerender(
      <CandlestickChart candles={[candle()]} accessibleLabel="AAPL chart" showVolume={false} />,
    );

    expect(volumeApplyOptions).toHaveBeenCalledWith({ visible: false });
    expect(priceScaleApplyOptions).toHaveBeenCalledWith({
      scaleMargins: { top: 0.1, bottom: 0.1 },
    });
  });

  it("updates the last volume point instead of resetting for a volume-only change", () => {
    const view = render(
      <CandlestickChart candles={[candle()]} accessibleLabel="AAPL chart" showVolume />,
    );
    priceSetData.mockClear();
    volumeSetData.mockClear();
    priceUpdate.mockClear();
    volumeUpdate.mockClear();

    act(() => {
      view.rerender(
        <CandlestickChart
          candles={[candle({ volume: 1_500 })]}
          accessibleLabel="AAPL chart"
          showVolume
        />,
      );
    });

    expect(volumeUpdate).toHaveBeenCalledWith(expect.objectContaining({ value: 1_500 }));
    expect(priceUpdate).toHaveBeenCalledOnce();
    expect(volumeSetData).not.toHaveBeenCalled();
    expect(priceSetData).not.toHaveBeenCalled();
  });
});
