import { ChartPanel } from "@/components/ChartPanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { getApiBaseUrl } from "@/lib/env";
import {
  CANDLE_INTERVALS,
  CHART_PERIODS,
  isCombinationSupported,
  supportedPeriodsForInterval,
  type CandleInterval,
  type ChartPeriod,
} from "@/lib/marketData";

type ChartPageProps = {
  params: Promise<{ instrumentId: string }>;
  searchParams: Promise<{
    interval?: string | string[];
    period?: string | string[];
  }>;
};

export default async function ChartPage({ params, searchParams }: ChartPageProps) {
  const [{ instrumentId }, query] = await Promise.all([params, searchParams]);
  const interval = readInterval(query.interval);
  const requestedPeriod = readPeriod(query.period);
  const period = isCombinationSupported(interval, requestedPeriod)
    ? requestedPeriod
    : (supportedPeriodsForInterval(interval)[0] ?? requestedPeriod);

  return (
    <main>
      <h1>Stock Market Analyzer</h1>
      <ErrorBoundary>
        <ChartPanel
          apiBaseUrl={getApiBaseUrl()}
          instrumentId={instrumentId}
          initialInterval={interval}
          initialPeriod={period}
        />
      </ErrorBoundary>
    </main>
  );
}

function readInterval(value: string | string[] | undefined): CandleInterval {
  const candidate = Array.isArray(value) ? value[0] : value;
  return CANDLE_INTERVALS.includes(candidate as CandleInterval)
    ? (candidate as CandleInterval)
    : "1d";
}

function readPeriod(value: string | string[] | undefined): ChartPeriod {
  const candidate = Array.isArray(value) ? value[0] : value;
  return CHART_PERIODS.includes(candidate as ChartPeriod) ? (candidate as ChartPeriod) : "1y";
}
