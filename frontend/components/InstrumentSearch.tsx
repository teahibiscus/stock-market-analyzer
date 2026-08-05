"use client";

import {
  type FormEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { Empty } from "@/components/state/Empty";
import { ErrorState } from "@/components/state/ErrorState";
import { Loading } from "@/components/state/Loading";
import {
  ApiClientError,
  type InstrumentSearchItem,
  type InstrumentSearchResponse,
  type SearchInstrumentsFunction,
  searchInstruments,
} from "@/lib/apiClient";

type SearchViewState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "results"; response: InstrumentSearchResponse }
  | { kind: "empty" }
  | { kind: "error"; message: string };

type InstrumentSearchProps = {
  apiBaseUrl: string;
  debounceMilliseconds?: number;
  onSelect?: (instrument: InstrumentSearchItem) => void;
  search?: SearchInstrumentsFunction;
};

export function InstrumentSearch({
  apiBaseUrl,
  debounceMilliseconds = 300,
  onSelect,
  search = searchInstruments,
}: InstrumentSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [viewState, setViewState] = useState<SearchViewState>({ kind: "idle" });
  const [selectedInstrument, setSelectedInstrument] = useState<InstrumentSearchItem | null>(null);
  const activeController = useRef<AbortController | null>(null);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestSequence = useRef(0);
  const sectionTitleId = useId();
  const inputId = useId();
  const helpId = useId();
  const validationId = useId();

  const clearDebounce = useCallback(() => {
    if (debounceTimer.current !== null) {
      clearTimeout(debounceTimer.current);
      debounceTimer.current = null;
    }
  }, []);

  const runSearch = useCallback(
    async (rawQuery: string) => {
      const normalizedQuery = rawQuery.trim();
      clearDebounce();
      if (!normalizedQuery) {
        setValidationMessage("Enter a symbol or company name.");
        return;
      }

      setValidationMessage(null);
      activeController.current?.abort();
      const controller = new AbortController();
      activeController.current = controller;
      const requestId = ++requestSequence.current;
      setViewState({ kind: "loading" });

      try {
        const response = await search(apiBaseUrl, normalizedQuery, controller.signal);
        if (controller.signal.aborted || requestId !== requestSequence.current) {
          return;
        }
        setViewState(
          response.metadata.state === "EMPTY" || response.items.length === 0
            ? { kind: "empty" }
            : { kind: "results", response },
        );
      } catch (error: unknown) {
        if (
          controller.signal.aborted ||
          requestId !== requestSequence.current ||
          (error instanceof DOMException && error.name === "AbortError")
        ) {
          return;
        }
        setViewState({
          kind: "error",
          message:
            error instanceof ApiClientError
              ? error.message
              : "Could not search instruments. Try again.",
        });
      }
    },
    [apiBaseUrl, clearDebounce, search],
  );

  useEffect(
    () => () => {
      clearDebounce();
      activeController.current?.abort();
      requestSequence.current += 1;
    },
    [clearDebounce],
  );

  function handleQueryChange(value: string) {
    setQuery(value);
    setValidationMessage(null);
    clearDebounce();
    activeController.current?.abort();
    requestSequence.current += 1;

    if (!value.trim()) {
      setViewState({ kind: "idle" });
      return;
    }

    debounceTimer.current = setTimeout(() => {
      void runSearch(value);
    }, debounceMilliseconds);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(query);
  }

  function selectInstrument(instrument: InstrumentSearchItem) {
    setSelectedInstrument(instrument);
    onSelect?.(instrument);
    router.push(`/chart/${encodeURIComponent(instrument.instrumentId)}?interval=1d&period=1y`);
  }

  function handleResultKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    instrument: InstrumentSearchItem,
  ) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectInstrument(instrument);
    }
  }

  const isLoading = viewState.kind === "loading";
  const describedBy = validationMessage ? `${helpId} ${validationId}` : helpId;

  return (
    <section className="instrument-search" aria-labelledby={sectionTitleId}>
      <h2 id={sectionTitleId}>Find an instrument</h2>
      <form role="search" onSubmit={handleSubmit} noValidate>
        <label htmlFor={inputId}>Symbol or company name</label>
        <div className="search-controls">
          <input
            id={inputId}
            type="search"
            value={query}
            maxLength={100}
            autoComplete="off"
            aria-describedby={describedBy}
            aria-invalid={validationMessage !== null}
            onBlur={() => {
              if (query && !query.trim()) {
                setValidationMessage("Enter a symbol or company name.");
              }
            }}
            onChange={(event) => handleQueryChange(event.target.value)}
          />
          <button type="submit" disabled={!query.trim() || isLoading}>
            Search instruments
          </button>
        </div>
        <p id={helpId} className="search-help">
          Enter a ticker symbol such as AAPL or a company name.
        </p>
        {validationMessage ? (
          <p id={validationId} role="alert" className="validation-message">
            {validationMessage}
          </p>
        ) : null}
      </form>

      <div className="search-state" aria-busy={isLoading}>
        {viewState.kind === "loading" ? <Loading message="Searching instruments…" /> : null}
        {viewState.kind === "empty" ? (
          <Empty message="No matching instruments. Try another symbol or company name." />
        ) : null}
        {viewState.kind === "error" ? (
          <>
            <ErrorState message={viewState.message} />
            <button type="button" onClick={() => void runSearch(query)}>
              Retry search
            </button>
          </>
        ) : null}
        {viewState.kind === "results" ? (
          <>
            <p aria-live="polite">
              {viewState.response.items.length} matching{" "}
              {viewState.response.items.length === 1 ? "instrument" : "instruments"}
            </p>
            <ul className="instrument-results" aria-label="Instrument search results">
              {viewState.response.items.map((instrument) => (
                <li key={instrument.instrumentId}>
                  <button
                    type="button"
                    className="instrument-result"
                    aria-label={`Select ${instrument.symbol}, ${instrument.companyName}, ${instrument.exchange}`}
                    aria-pressed={selectedInstrument?.instrumentId === instrument.instrumentId}
                    onClick={() => selectInstrument(instrument)}
                    onKeyDown={(event) => handleResultKeyDown(event, instrument)}
                  >
                    <strong>{instrument.symbol}</strong>
                    <span>{instrument.companyName}</span>
                    <span>
                      {instrument.exchange} · {instrument.assetType}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>

      {selectedInstrument ? (
        <p className="selected-instrument" aria-live="polite">
          Selected {selectedInstrument.symbol} — {selectedInstrument.companyName}
        </p>
      ) : null}
    </section>
  );
}
