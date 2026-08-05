import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChartPage from "./page";

vi.mock("@/components/ChartPanel", () => ({
  ChartPanel: (props: {
    apiBaseUrl: string;
    instrumentId: string;
    initialInterval: string;
    initialPeriod: string;
  }) => <div data-testid="chart-panel">{JSON.stringify(props)}</div>,
}));

vi.mock("@/components/ErrorBoundary", () => ({
  ErrorBoundary: ({ children }: { children: ReactNode }) => children,
}));

vi.mock("@/lib/env", () => ({
  getApiBaseUrl: () => "http://api.test",
}));

describe("ChartPage", () => {
  it("passes the route instrument and supported query parameters to the chart", async () => {
    render(
      await ChartPage({
        params: Promise.resolve({ instrumentId: "instrument-aapl" }),
        searchParams: Promise.resolve({ interval: "1d", period: "1y" }),
      }),
    );

    expect(screen.getByTestId("chart-panel")).toHaveTextContent(
      JSON.stringify({
        apiBaseUrl: "http://api.test",
        instrumentId: "instrument-aapl",
        initialInterval: "1d",
        initialPeriod: "1y",
      }),
    );
  });

  it("falls back to a compatible period for invalid query combinations", async () => {
    render(
      await ChartPage({
        params: Promise.resolve({ instrumentId: "instrument-aapl" }),
        searchParams: Promise.resolve({ interval: "1m", period: "1y" }),
      }),
    );

    expect(screen.getByTestId("chart-panel")).toHaveTextContent('"initialInterval":"1m"');
    expect(screen.getByTestId("chart-panel")).toHaveTextContent('"initialPeriod":"1d"');
  });
});
