import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { InstrumentSearchResponse, SearchInstrumentsFunction } from "@/lib/apiClient";

import { InstrumentSearch } from "./InstrumentSearch";

const successResponse: InstrumentSearchResponse = {
  items: [
    {
      instrumentId: "instrument-aapl",
      symbol: "AAPL",
      companyName: "Apple Inc.",
      exchange: "NASDAQ",
      assetType: "EQUITY",
      status: "ACTIVE",
    },
  ],
  metadata: {
    state: "SUCCESS",
    code: "INSTRUMENT_SEARCH_SUCCESS",
    recoverable: false,
    retryAfterSeconds: null,
    freshness: null,
    warnings: [],
  },
};

const emptyResponse: InstrumentSearchResponse = {
  items: [],
  metadata: {
    state: "EMPTY",
    code: "INSTRUMENT_SEARCH_EMPTY",
    recoverable: true,
    retryAfterSeconds: null,
    freshness: null,
    warnings: [],
  },
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

afterEach(() => {
  vi.useRealTimers();
});

describe("InstrumentSearch", () => {
  it("provides a labelled, constrained search control and clear validation", () => {
    const search = vi.fn<SearchInstrumentsFunction>();
    render(<InstrumentSearch apiBaseUrl="http://api.test" search={search} />);

    const input = screen.getByRole("searchbox", {
      name: "Symbol or company name",
    });
    const submit = screen.getByRole("button", { name: "Search instruments" });

    expect(input).toHaveAttribute("maxLength", "100");
    expect(submit).toBeDisabled();

    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.blur(input);

    expect(screen.getByRole("alert")).toHaveTextContent("Enter a symbol or company name.");
    expect(search).not.toHaveBeenCalled();
  });

  it("shows loading, renders identifying result details, and supports keyboard selection", async () => {
    const request = deferred<InstrumentSearchResponse>();
    const search = vi.fn<SearchInstrumentsFunction>().mockReturnValue(request.promise);
    render(<InstrumentSearch apiBaseUrl="http://api.test" search={search} />);

    fireEvent.change(screen.getByRole("searchbox", { name: "Symbol or company name" }), {
      target: { value: "Apple" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search instruments" }));

    expect(screen.getByRole("status")).toHaveTextContent("Searching instruments…");

    await act(async () => {
      request.resolve(successResponse);
      await request.promise;
    });

    const option = screen.getByRole("button", {
      name: "Select AAPL, Apple Inc., NASDAQ",
    });
    expect(option).toHaveTextContent("AAPL");
    expect(option).toHaveTextContent("Apple Inc.");
    expect(option).toHaveTextContent("NASDAQ");

    option.focus();
    fireEvent.keyDown(option, { key: "Enter" });

    expect(option).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Selected AAPL — Apple Inc.")).toBeVisible();
  });

  it("shows an actionable empty state", async () => {
    const search = vi.fn<SearchInstrumentsFunction>().mockResolvedValue(emptyResponse);
    render(<InstrumentSearch apiBaseUrl="http://api.test" search={search} />);

    fireEvent.change(screen.getByRole("searchbox", { name: "Symbol or company name" }), {
      target: { value: "unknown" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search instruments" }));

    expect(
      await screen.findByText("No matching instruments. Try another symbol or company name."),
    ).toBeVisible();
  });

  it("shows recoverable errors and retries without clearing the query", async () => {
    const search = vi
      .fn<SearchInstrumentsFunction>()
      .mockRejectedValueOnce(new Error("service unavailable"))
      .mockResolvedValueOnce(successResponse);
    render(<InstrumentSearch apiBaseUrl="http://api.test" search={search} />);

    const input = screen.getByRole("searchbox", {
      name: "Symbol or company name",
    });
    fireEvent.change(input, { target: { value: "Apple" } });
    fireEvent.click(screen.getByRole("button", { name: "Search instruments" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not search instruments. Try again.",
    );
    expect(input).toHaveValue("Apple");

    fireEvent.click(screen.getByRole("button", { name: "Retry search" }));

    expect(
      await screen.findByRole("button", {
        name: "Select AAPL, Apple Inc., NASDAQ",
      }),
    ).toBeVisible();
    expect(search).toHaveBeenCalledTimes(2);
  });

  it("aborts superseded debounced requests and suppresses stale results", async () => {
    vi.useFakeTimers();
    const first = deferred<InstrumentSearchResponse>();
    const second = deferred<InstrumentSearchResponse>();
    const signals: AbortSignal[] = [];
    const search = vi
      .fn<SearchInstrumentsFunction>()
      .mockImplementation((_baseUrl, _query, signal) => {
        signals.push(signal);
        return signals.length === 1 ? first.promise : second.promise;
      });
    render(
      <InstrumentSearch apiBaseUrl="http://api.test" debounceMilliseconds={300} search={search} />,
    );
    const input = screen.getByRole("searchbox", {
      name: "Symbol or company name",
    });

    fireEvent.change(input, { target: { value: "A" } });
    await act(() => {
      vi.advanceTimersByTime(300);
      return Promise.resolve();
    });
    expect(search).toHaveBeenCalledTimes(1);

    fireEvent.change(input, { target: { value: "Apple" } });
    await act(() => {
      vi.advanceTimersByTime(300);
      return Promise.resolve();
    });
    expect(search).toHaveBeenCalledTimes(2);
    expect(signals[0]?.aborted).toBe(true);

    await act(async () => {
      first.resolve(successResponse);
      await first.promise;
    });
    expect(screen.queryByText("Apple Inc.")).not.toBeInTheDocument();

    await act(async () => {
      second.resolve(emptyResponse);
      await second.promise;
    });
    expect(
      screen.getByText("No matching instruments. Try another symbol or company name."),
    ).toBeVisible();
  });
});
