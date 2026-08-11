# Stock Market Analyzer

A professional stock-market charting application being delivered incrementally from the repository's
product requirements. The MVP will provide symbol discovery, market-data context, charting,
indicators, watchlists, persistence, and operational reliability. Scanning, alerts, AI-assisted
analysis, and backtesting remain future capabilities.

## Current status

The repository foundation, application shells, shared contracts, and instrument catalog are now
implemented:

- FastAPI application with composition root and `/api/v1` router
- `/health` liveness and `/ready` readiness endpoints with PostgreSQL and Redis checks
- Structured logging and correlation-ID middleware
- Next.js application shell with typed API client and accessible state components
- Backend health probe on the home page
- Worker backfill command and scheduler entry-point placeholder
- Shared application-state, freshness, typed-error, identifier, and time contracts
- Instrument domain and provider port with deterministic local reference data
- Alembic-managed `instruments` schema with exchanges, instruments, symbols, and search indexes
- SQLAlchemy instrument repository with symbol and company-name matching
- `GET /api/v1/instruments/search` with validation, typed states, errors, and telemetry
- Accessible search UI with debounce, cancellation, retry, result selection, and responsive layout
- PostgreSQL-backed raw OHLCV bars with idempotent demo-data backfill
- Canonical `GET /api/v1/charts/{instrument_id}` chart read path with read-through persistence
- Search-to-chart navigation for every seeded instrument and bounded SSE demo updates
- Interval and period controls with compatibility enforcement and responsive chart sizing
- Volume histogram overlay with a keyboard-accessible toggle and an unavailable-volume state

The database-backed instrument-search and persisted candlestick-chart vertical slices are complete.

## Prerequisites

- Python 3.12 or newer
- Node.js 22 or newer
- Docker Desktop with Docker Compose

## Install

Create a local environment file and replace the example-only database password:

```powershell
Copy-Item .env.example .env
```

Create and activate a Python virtual environment, then install backend development tooling:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".\backend[dev]"
```

Install frontend tooling from the repository root:

```powershell
npm install
```

## Run local services

Start PostgreSQL and Redis:

```powershell
docker compose up -d
docker compose ps
```

Stop the services without deleting their data:

```powershell
docker compose down
```

Apply the current database migrations from the repository root:

```powershell
.\.venv\Scripts\alembic.exe -c backend/alembic.ini upgrade head
```

The example reserves ports 8000 and 3000 for the backend and frontend processes.

## Run backend API

Start PostgreSQL and Redis first, then run the API from the repository root:

```powershell
docker compose up -d
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[dev]"
stock-market-analyzer-api
```

Or:

```powershell
python -m stock_market_analyzer.app.main
```

Verify endpoints:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/v1
curl "http://127.0.0.1:8000/api/v1/instruments/search?q=AAPL"
```

## Run frontend

From the repository root:

```powershell
npm install
npm run dev --workspace frontend
```

Open `http://localhost:3000` (primary) or `http://127.0.0.1:3000` to use instrument search,
select an instrument, open its chart, and view the backend health probe. The backend CORS allow-list
permits both local origins.

## Run the chart locally

Create `.env`, start dependencies, and apply migrations from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d --wait
.\.venv\Scripts\alembic.exe -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m stock_market_analyzer.worker backfill --interval 1d --period 1y
```

Start the backend in one terminal:

```powershell
.\.venv\Scripts\python.exe -m stock_market_analyzer.app.main
```

Start the frontend in another terminal:

```powershell
npm run dev --workspace frontend
```

Search for a seeded instrument and select it. The application navigates to a URL-addressable chart,
loads canonical bars from PostgreSQL, and continuously replaces the active candle from a bounded SSE
stream. All chart prices are **simulated demo data, not live exchange market data**. Demo responses
are explicitly marked `STALE` with a `SYNTHETIC_MARKET_DATA` warning.

History and stream endpoints:

```text
GET http://127.0.0.1:8000/api/v1/charts/00000000-0000-4000-8000-000000000002?interval=1d&period=1y
GET http://127.0.0.1:8000/api/v1/market-data/stream?symbol=AAPL&interval=1m
```

Supported intervals are `1m`, `2m`, `5m`, `15m`, `30m`, `1h`, and `1d`. Supported periods are
`1d`, `5d`, `1mo`, `3mo`, `6mo`, and `1y`. The period control disables combinations the backend
does not support. Changing to an interval incompatible with the selected period automatically picks
that interval's first compatible period.

Volume is drawn as a histogram overlay pinned to the lower band of the price pane and coloured by
candle direction. The **Show volume** toggle hides it without refetching history, and the choice is
URL-addressable through `volume=0` or `volume=1`:

```text
http://localhost:3000/chart/00000000-0000-4000-8000-000000000002?interval=1d&period=1y&volume=0
```

When a timeframe returns candles whose volume is entirely zero or absent, the chart keeps rendering
prices, disables the toggle, and shows an explicit unavailable-volume badge rather than an empty
band.

Known chart limitations: there is no production market-data provider, entitlement enforcement, or
missed-event replay. The SSE endpoint is demo-only and bounded by connection-count and duration
limits. Volume is reported as raw provider counts with no split or dividend adjustment.

## Test the vertical slice locally

Prepare and migrate the services from the repository root:

```powershell
Copy-Item .env.example .env -ErrorAction SilentlyContinue
docker compose up -d --wait
.\.venv\Scripts\alembic.exe -c backend/alembic.ini upgrade head
```

Start the API in one terminal:

```powershell
.\.venv\Scripts\Activate.ps1
stock-market-analyzer-api
```

Start the frontend in a second terminal:

```powershell
npm run dev --workspace frontend
```

Open `http://127.0.0.1:3000`, then try:

- `AAPL` for an exact symbol match
- `Microsoft` for a company-name match
- `unknown` for the empty state
- Entering a query and quickly replacing it to exercise request cancellation
- Selecting a result with Tab followed by Enter

The API can also be checked directly:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/instruments/search?q=Apple"
```

## Validate

Backend:

```powershell
ruff format --check backend
ruff check backend
mypy --config-file backend/pyproject.toml backend/src backend/tests
pytest -c backend/pyproject.toml backend/tests
python -m build backend
```

Frontend and repository contract:

```powershell
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Validate the service definition without starting containers:

```powershell
docker compose --env-file .env.example config --quiet
```

## Architecture

The backend is a modular monolith. Its API, worker, and scheduler will share one versioned Python
package while running as separate processes. Domain modules publish application interfaces and own
their schemas; they do not access another module's private tables.

PostgreSQL is the MVP system of record. Redis is disposable and is used only for caching, rate limits,
and short-lived read acceleration. External identity and market-data systems will be isolated behind
ports and adapters so vendor DTOs do not leak into canonical domain contracts.

### Delivery platform decision

The MVP is a responsive web application. Desktop packaging (Tauri or Electron) and PWA installation
are deliberately postponed rather than rejected. Canvas rendering through `lightweight-charts` is not
the current performance constraint, and a desktop shell would add code signing, an update channel,
and a second CI matrix before there is a deployed web instance to validate demand against. Offline
support has little value for live market data.

Two invariants keep the deferral cheap, and both hold today:

- The frontend reaches the backend only over HTTP and SSE through the configurable
  `NEXT_PUBLIC_API_BASE_URL`, so it can point at a locally hosted API unchanged.
- Chart state (instrument, interval, period, volume visibility) is URL-addressable, so window and
  workspace restoration needs no new persistence layer.

Revisit after the web MVP is validated, once watchlists and indicators make multi-window and
multi-monitor workflows worth the packaging cost. The concrete blocker to resolve then is that
`frontend/next.config.ts` sets neither `output: "export"` nor `output: "standalone"`.

The initial directory layout is intentionally small:

```text
backend/
  migrations/
  src/stock_market_analyzer/
  tests/
frontend/
  app/
  components/
  lib/
architecture/
product-requirements/
```

Only directories containing working configuration, code, or tests are created. Bounded-context
directories will be added when their first behavior is implemented.

## Requirements workflow

`product-requirements/MANIFEST.md` is the source of truth for epic, feature, story, phase, and file
location. Implementation work follows this order:

1. Read the selected story PRD.
2. Read its parent feature and epic only when needed for scope.
3. Confirm MVP or future classification in the manifest.
4. Map acceptance criteria to tests before implementation.
5. Keep future-phase stories out of MVP delivery unless Product explicitly promotes them.

The completed first vertical slice covers `E01-F01-S01` and `E01-F01-S02`: database-backed symbol
and company search with accessible loading, success, empty, validation, error, retry, cancellation,
and selection behavior.

Charting work delivered so far covers `E02-F01` core price rendering, `E02-F03` timeframes and
intervals, and `E02-F06-S01` volume display. The next chart story is `E02-F05-S01`, crosshair and
data inspection.

## TDD and CI

Each task starts with the smallest test that describes its contract. Unit, integration, contract,
architecture, and end-to-end tests are added in proportion to the behavior being introduced.

CI currently checks the repository contract and Docker Compose configuration, then runs backend and
frontend formatting, linting, type checking, tests, and build validation. Security scanning,
container builds, and deployment stages remain deferred.

## Deferred work

- Authentication, production provider integrations, ingestion, indicators, and watchlists
- Market-data entitlements, SSE heartbeat, and missed-event replay
- Managed queue, object storage, secrets manager, and production observability integrations

The next story should be selected from `product-requirements/MANIFEST.md` and scoped from its PRDs
before implementation.
