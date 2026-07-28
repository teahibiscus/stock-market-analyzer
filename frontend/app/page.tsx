import { ChartPanel } from "@/components/ChartPanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { HealthProbe } from "@/components/HealthProbe";
import { InstrumentSearch } from "@/components/InstrumentSearch";
import { getApiBaseUrl } from "@/lib/env";

export default function HomePage() {
  const apiBaseUrl = getApiBaseUrl();

  return (
    <main>
      <h1>Stock Market Analyzer</h1>
      <p>Search the supported instrument catalog by ticker or company name.</p>
      <ErrorBoundary>
        <InstrumentSearch apiBaseUrl={apiBaseUrl} />
      </ErrorBoundary>
      <ErrorBoundary>
        <ChartPanel apiBaseUrl={apiBaseUrl} symbol="AAPL" />
      </ErrorBoundary>
      <ErrorBoundary>
        <HealthProbe />
      </ErrorBoundary>
    </main>
  );
}
