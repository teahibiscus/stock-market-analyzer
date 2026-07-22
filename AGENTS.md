# Prompt: Generate the Initial Codebase for the Stock Market Charting Application (Claude Free Plan Optimized)

Act as a senior software engineer, software architect, FinTech engineer, DevOps engineer, QA engineer, and AI coding assistant.

You are running on the free version of Claude. Optimize your work for limited context, limited message length, and limited execution time.

Your goal is not to generate the entire production application in one response. Your goal is to create a strong initial foundation through small, verifiable implementation steps.

Work incrementally.

Do not attempt to read, analyze, and rewrite the entire repository at once if the repository is large.

Prioritize:

1. Understanding the architecture and PRD structure
2. Creating the project foundation
3. Implementing one working vertical slice
4. Validating the implementation
5. Clearly documenting what remains

---

# Important Claude Free Plan Operating Rules

Because context and response limits may be constrained:

## Work in phases

Do not attempt all phases in one pass.

Complete work in this order:

### Phase A — Repository understanding

Only:

- Inspect repository structure
- Read architecture documentation
- Read `README.md`
- Read `MANIFEST.md`
- Read the relevant PRDs for the first implementation slice
- Identify existing technology choices

Then summarize findings before making large changes.

---

### Phase B — Foundation scaffolding

Create only the minimum required foundation:

- Backend application skeleton
- Frontend application skeleton
- Configuration handling
- Database connection setup
- Migration framework
- Local development environment
- Basic testing setup
- Documentation updates

Do not implement every future module.

---

### Phase C — First vertical slice

Implement only:

- Instrument search
- Symbol/company lookup
- Backend API
- Database-backed repository
- Frontend search UI
- Tests

Do not move to charts, indicators, watchlists, authentication, or market-data ingestion until this slice is complete.

---

### Phase D — Review and next steps

After completing the first slice:

- Run validation
- Summarize changes
- Identify remaining work
- Recommend the next story

---

# 1. Project Context

This project is a professional stock market charting application.

The long-term product includes:

- Symbol and company search
- Instrument metadata
- Quote summaries
- Market-session context
- Market-data freshness indicators
- Interactive price and volume charts
- Chart types, intervals, and timeframes
- Zoom, pan, and chart inspection
- Chart appearance and templates
- Technical indicators
- Watchlists
- Data grids
- User accounts
- Permissions
- Reliability and observability
- Market-data provider integrations
- Historical market-data management
- Corporate actions
- Future scanning
- Future alerts
- Future AI-assisted analysis
- Future backtesting

However, the initial implementation must focus only on creating a reliable foundation and one working MVP workflow.

Do not attempt to build the entire product.

---

# 2. Authoritative Project Inputs

Before writing code, inspect project documentation.

Use this priority order:

1. Story PRD being implemented
2. Parent feature PRD
3. Parent epic PRD
4. `MANIFEST.md`
5. PRD package README
6. Official software architecture
7. Project-level Claude instructions
8. Repository folder structure
9. Existing source code
10. Current task instructions

`MANIFEST.md` is the source of truth for:

- Epic IDs
- Feature IDs
- Story IDs
- MVP scope
- Future scope
- PRD locations

Do not implement future-phase requirements unless they are required to support the current MVP slice.

Do not infer requirements from names alone.

Read the actual PRDs.

---

# 3. Repository Folder Structure

Use the repository structure supplied by the user:

```text
[PASTE THE COMPLETE REPOSITORY FOLDER BREAKDOWN HERE]
```

Treat this as the intended layout.

Before creating files:

1. Compare it with the architecture.
2. Identify missing folders required for a runnable application.
3. Preserve existing organization.
4. Avoid unnecessary restructuring.
5. Add only required folders.
6. Avoid creating empty placeholder directories.

If the repository already contains code:

- Inspect before modifying.
- Preserve working implementations.
- Do not overwrite files blindly.

---

# 4. Initial Implementation Goal

Create a minimal but professional foundation.

The initial codebase should:

- Run locally
- Have frontend and backend entry points
- Follow modular-monolith architecture
- Establish bounded-context boundaries
- Support future API, worker, and scheduler processes
- Include PostgreSQL integration
- Include Redis integration points
- Include configuration management
- Include migrations
- Include health checks
- Include structured logging
- Include typed errors
- Include testing infrastructure
- Include local development setup
- Include documentation

Do not create large amounts of unused scaffolding.

Prefer working code over empty architecture folders.

---

# 5. Technology Selection

First inspect the repository.

If technologies already exist:

- Keep them.
- Follow existing conventions.

If no stack exists, use:

## Frontend

- TypeScript
- React
- Next.js
- Accessible components
- Typed API client

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Pytest

## Tooling

- Docker Compose
- OpenAPI
- Environment configuration
- Structured logging

Do not introduce unnecessary dependencies.

For Claude Free Plan efficiency:

Prefer fewer libraries and simpler implementations.

---

# 6. Architecture Requirements

The backend should begin as a modular monolith.

Use bounded contexts such as:

```text
identity
authorization
instruments
quotes
charts
indicators
watchlists
market_data
corporate_actions
data_quality
diagnostics
application_state
```

Do not fully implement every module.

Only create meaningful code for modules required by the current slice.

Use this layering pattern where useful:

```text
domain/
application/
ports/
infrastructure/
api/
```

Rules:

- API handlers contain no business logic.
- Domain code does not import frameworks.
- Domain code does not import databases.
- External providers use adapters.
- Modules communicate through interfaces.
- Avoid circular dependencies.
- Keep shared utilities small.

---

# 7. First Vertical Slice: Instrument Search

Implement only the first MVP workflow.

The workflow:

User enters a symbol or company name.

The system:

1. Accepts the query.
2. Searches instruments.
3. Returns matching instruments.
4. Displays results.
5. Allows selection.

Implement:

## Frontend

- Search input
- Submit/debounce behavior
- Loading state
- Empty state
- Error state
- Results list
- Keyboard accessibility

## Backend

Endpoint:

```text
GET /api/v1/instruments/search?q={query}
```

Response:

```json
{
  "instrumentId": "123",
  "symbol": "AAPL",
  "companyName": "Apple Inc.",
  "exchange": "NASDAQ",
  "assetType": "EQUITY",
  "status": "ACTIVE"
}
```

## Database

Create:

```text
instruments
instrument_symbols
exchanges
```

Include:

- Internal instrument ID
- Symbol
- Company name
- Exchange
- Asset type
- Status
- Timestamps
- Search indexes

Use seed data.

Do not connect to external market-data providers yet.

---

# 8. Application State Contract

Create shared application states:

```text
LOADING
SUCCESS
EMPTY
UNAVAILABLE
DELAYED
VALIDATION_ERROR
PERMISSION_DENIED
TIMEOUT
DEPENDENCY_ERROR
PERSISTENCE_ERROR
PARTIAL_SUCCESS
```

Create freshness states:

```text
FRESH
DELAYED
STALE
UNAVAILABLE
UNKNOWN
```

Use only states relevant to the current workflow.

Create typed API errors containing:

- Error code
- Message
- HTTP status
- Correlation ID
- Recoverability

Never expose stack traces.

---

# 9. Backend Foundation

Create:

- Application startup
- Configuration
- API routing
- Health endpoint
- Readiness endpoint
- Logging
- Error handling
- Database sessions
- Migration support
- Redis abstraction
- Worker entry point placeholder
- Scheduler entry point placeholder

Do not implement real ingestion jobs yet.

---

# 10. Provider Boundary

Create interfaces for future providers.

Example:

```text
MarketDataProvider
InstrumentReferenceProvider
```

Requirements:

- Provider code isolated
- DTO translation
- Stable internal models
- No provider SDK leakage

Do not implement external integrations.

---

# 11. Frontend Foundation

Create:

- Application shell
- API client
- Environment configuration
- Error boundary
- Loading component
- Empty component
- Error component
- Search component
- Search results component

Avoid building a full design system.

---

# 12. Testing Requirements

Create tests for the implemented slice.

Minimum:

## Backend

- Query validation
- Search matching
- Empty results
- API response
- Error handling

## Frontend

- Search input
- Loading state
- Empty state
- Error state
- Result rendering

## Integration

- API against test database

## Architecture

Where practical:

- Domain isolation
- Provider isolation
- Dependency rules

Do not spend excessive time creating complex test infrastructure before the feature works.

---

# 13. Local Development

Create:

- Docker Compose
- PostgreSQL
- Redis
- Environment examples
- Migration commands
- Seed commands

Document:

- Install
- Run
- Test
- Build

Do not include secrets.

---

# 14. CI Foundation

Create lightweight CI.

Run:

1. Formatting
2. Linting
3. Type checks
4. Tests
5. Build validation

Avoid overly complex pipelines.

---

# 15. Documentation

Create or update:

## README.md

Include:

- Project overview
- Current implementation status
- Setup instructions
- Commands
- Architecture summary

## Architecture documentation

Include:

- Module boundaries
- Dependency rules
- Runtime processes

## PRD workflow documentation

Explain:

- Manifest usage
- Epic → Feature → Story flow
- Acceptance criteria mapping

## Initial implementation notes

Document:

- What works
- What is deferred
- Next recommended story

---

# 16. Scope Restrictions

Do not implement:

- Full chart engine
- Live streaming
- Historical ingestion
- Indicators
- Watchlists
- Alerts
- AI analysis
- Backtesting
- Kubernetes
- Kafka
- Data lake
- Trading execution

Only create extension points.

---

# 17. Code Rules

When modifying the repository:

- Create real files.
- Do not return only snippets.
- Avoid empty placeholder classes.
- Use strong typing.
- Keep functions focused.
- Add tests.
- Preserve existing files.
- Do not delete files unnecessarily.
- Do not run destructive commands.
- Do not claim success without validation.

---

# 18. Execution Strategy for Claude Free

Because of context limitations:

After each major phase, stop and summarize.

Use this checkpoint pattern:

## Checkpoint 1

Report:

- Files inspected
- Architecture understanding
- Technology choices
- Implementation plan

Wait for confirmation if the repository is large.

## Checkpoint 2

Report:

- Files created
- Foundation status
- Remaining work

## Checkpoint 3

Report:

- Vertical slice status
- Tests run
- Issues found

Continue only when enough context remains.

---

# 19. Final Response Format

After completing the current phase, provide:

## Summary

What was implemented.

## Files Changed

Grouped by:

- Frontend
- Backend
- Database
- Infrastructure
- Tests
- Documentation

## Working Features

Describe what works.

## PRD Traceability

| Requirement | Implementation | Test |
| ----------- | -------------- | ---- |

## Validation

Separate:

- Passed
- Failed
- Not run

## Assumptions

List reversible decisions.

## Deferred Work

List intentionally postponed items.

## Recommended Next Step

Recommend the next implementation story.

---

# 20. Completion Standard

The task is complete when:

- The repository has a runnable foundation.
- The first vertical slice works.
- Local setup is documented.
- Tests exist.
- Architecture boundaries are represented.
- Future features remain extension points.
- The final report honestly describes the current state.

Begin by inspecting the repository and project documents.

Do not attempt to generate the entire application in one response. Work incrementally and preserve context.
