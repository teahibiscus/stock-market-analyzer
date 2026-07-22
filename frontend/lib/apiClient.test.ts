import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, fetchHealth, searchInstruments } from "./apiClient";

describe("fetchHealth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the health payload when the API responds successfully", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: "ok" }),
      }),
    );

    await expect(fetchHealth("http://127.0.0.1:8000")).resolves.toEqual({
      status: "ok",
    });
  });

  it("throws when the API responds with a non-success status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
      }),
    );

    await expect(fetchHealth("http://127.0.0.1:8000")).rejects.toThrow(
      "Health check failed with status 503",
    );
  });
});

describe("searchInstruments", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("encodes the trimmed query and forwards the abort signal", async () => {
    const signal = new AbortController().signal;
    const payload = {
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
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(payload),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      searchInstruments("http://127.0.0.1:8000/", " Apple Inc. ", signal),
    ).resolves.toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/instruments/search?q=Apple+Inc.",
      {
        headers: { Accept: "application/json" },
        signal,
      },
    );
  });

  it("throws a typed recoverable error from problem details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: () =>
          Promise.resolve({
            code: "PERSISTENCE_ERROR",
            detail: "Instrument search is temporarily unavailable.",
            correlationId: "search-correlation",
            recoverable: true,
          }),
      }),
    );

    const error = await searchInstruments(
      "http://127.0.0.1:8000",
      "AAPL",
      new AbortController().signal,
    ).catch((reason: unknown) => reason);

    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "PERSISTENCE_ERROR",
      correlationId: "search-correlation",
      message: "Instrument search is temporarily unavailable.",
      recoverable: true,
      status: 503,
    });
  });
});
