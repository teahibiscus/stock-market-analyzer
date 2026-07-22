export type HealthResponse = {
  status: "ok";
};

export type ApplicationState =
  | "LOADING"
  | "SUCCESS"
  | "EMPTY"
  | "UNAVAILABLE"
  | "DELAYED"
  | "VALIDATION_ERROR"
  | "PERMISSION_DENIED"
  | "TIMEOUT"
  | "DEPENDENCY_ERROR"
  | "PERSISTENCE_ERROR"
  | "PARTIAL_SUCCESS";

export type InstrumentSearchItem = {
  instrumentId: string;
  symbol: string;
  companyName: string;
  exchange: string;
  assetType: "EQUITY" | "ETF";
  status: "ACTIVE" | "INACTIVE";
};

export type ApplicationStateMetadata = {
  state: ApplicationState;
  code: string;
  recoverable: boolean;
  retryAfterSeconds: number | null;
  freshness: {
    providerTimestamp: string | null;
    ingestedAt: string | null;
    delaySeconds: number | null;
    state: "FRESH" | "DELAYED" | "STALE" | "UNAVAILABLE" | "UNKNOWN" | null;
  } | null;
  warnings: string[];
};

export type InstrumentSearchResponse = {
  items: InstrumentSearchItem[];
  metadata: ApplicationStateMetadata;
};

type ProblemDetails = {
  code?: string;
  detail?: string;
  correlationId?: string;
  recoverable?: boolean;
};

export class ApiClientError extends Error {
  readonly code: string;
  readonly status: number;
  readonly correlationId: string | null;
  readonly recoverable: boolean;

  constructor(
    message: string,
    options: {
      code: string;
      status: number;
      correlationId?: string | null;
      recoverable?: boolean;
    },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = options.code;
    this.status = options.status;
    this.correlationId = options.correlationId ?? null;
    this.recoverable = options.recoverable ?? false;
  }
}

export type SearchInstrumentsFunction = (
  baseUrl: string,
  query: string,
  signal: AbortSignal,
) => Promise<InstrumentSearchResponse>;

export async function fetchHealth(baseUrl: string): Promise<HealthResponse> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}

export const searchInstruments: SearchInstrumentsFunction = async (baseUrl, query, signal) => {
  const url = new URL(`${baseUrl.replace(/\/$/, "")}/api/v1/instruments/search`);
  url.searchParams.set("q", query.trim());

  const response = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    let problem: ProblemDetails = {};
    try {
      problem = (await response.json()) as ProblemDetails;
    } catch {
      // A transport-safe fallback is returned below.
    }
    throw new ApiClientError(
      problem.detail ?? `Instrument search failed with status ${response.status}`,
      {
        code: problem.code ?? "DEPENDENCY_ERROR",
        correlationId: problem.correlationId,
        recoverable: problem.recoverable,
        status: response.status,
      },
    );
  }

  return (await response.json()) as InstrumentSearchResponse;
};
