import { ApiClientError, type ApplicationStateMetadata } from "./apiClient";

export const CANDLE_INTERVALS = ["1m", "2m", "5m", "15m", "30m", "1h", "1d"] as const;
export const CHART_PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y"] as const;

export type CandleInterval = (typeof CANDLE_INTERVALS)[number];
export type ChartPeriod = (typeof CHART_PERIODS)[number];

export type MarketCandle = {
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
};

export type CandleHistoryResponse = {
  symbol: string;
  interval: CandleInterval;
  period: ChartPeriod;
  timezone: "UTC";
  dataSource: string;
  asOf: string;
  candles: MarketCandle[];
  metadata: ApplicationStateMetadata;
};

export type StreamCandleUpdate = MarketCandle & {
  symbol: string;
  interval: CandleInterval;
  eventTimestamp: string;
  sequence: number;
};

const SUPPORTED_PERIODS = {
  "1m": ["1d", "5d"],
  "2m": ["1d", "5d"],
  "5m": ["1d", "5d", "1mo"],
  "15m": ["1d", "5d", "1mo"],
  "30m": ["1d", "5d", "1mo"],
  "1h": ["1d", "5d", "1mo", "3mo", "6mo"],
  "1d": ["1mo", "3mo", "6mo", "1y"],
} as const satisfies Record<CandleInterval, readonly ChartPeriod[]>;

type ProblemDetails = {
  code?: string;
  detail?: string;
  correlationId?: string;
  recoverable?: boolean;
};

export function supportedPeriodsForInterval(interval: CandleInterval): readonly ChartPeriod[] {
  return SUPPORTED_PERIODS[interval];
}

export function isCombinationSupported(interval: CandleInterval, period: ChartPeriod): boolean {
  return supportedPeriodsForInterval(interval).some(
    (supportedPeriod) => supportedPeriod === period,
  );
}

export async function fetchCandles(
  baseUrl: string,
  symbol: string,
  interval: CandleInterval,
  period: ChartPeriod,
  signal: AbortSignal,
): Promise<CandleHistoryResponse> {
  if (!isCombinationSupported(interval, period)) {
    throw new ApiClientError(`Interval ${interval} is not supported for period ${period}.`, {
      code: "VALIDATION_ERROR",
      recoverable: true,
      status: 422,
    });
  }

  const url = new URL(`${baseUrl.replace(/\/$/, "")}/api/v1/market-data/candles`);
  url.searchParams.set("symbol", symbol.trim().toUpperCase());
  url.searchParams.set("interval", interval);
  url.searchParams.set("period", period);

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
      problem.detail ?? `Candle history request failed with status ${response.status}`,
      {
        code: problem.code ?? "DEPENDENCY_ERROR",
        correlationId: problem.correlationId,
        recoverable: problem.recoverable,
        status: response.status,
      },
    );
  }

  return (await response.json()) as CandleHistoryResponse;
}
