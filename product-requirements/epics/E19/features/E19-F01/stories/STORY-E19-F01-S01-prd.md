# Story PRD: E19-F01-S01 - Load Existing Web UI in Electron

## 1. Document Control

| Field | Value |
|---|---|
| Document Type | Story PRD |
| Epic ID | E19 |
| Feature ID | E19-F01 |
| Story ID | E19-F01-S01 |
| Story Name | Load Existing Web UI in Electron |
| Status | Draft |
| Last Updated | 2026-08-25 |
| Priority / Phase | MVP |
| MVP Scope | Yes |
| Release Treatment | Required for desktop MVP |

## 2. User Story

As an active trader, I want to launch the existing analyzer in a desktop shell so that I can search
symbols, inspect charts, and receive live updates without manually opening a browser.

## 3. Scope

### In Scope

- Electron loads the existing Next.js routes.
- Local API and frontend services are reused or started and health-checked.
- Search-to-chart navigation, chart history, and SSE continue unchanged.
- Renderer security defaults and trusted-origin navigation are enforced.
- Owned child processes stop when the application quits.

### Out of Scope

- Installation, code signing, updates, bundled infrastructure, and saved workspaces.
- Authentication, production providers, alerts, scanning, and AI.

## 4. Functional Requirements

| Requirement ID | Requirement |
|---|---|
| FR-E19-F01-S01-001 | Launching the desktop command shall make the existing frontend available. |
| FR-E19-F01-S01-002 | The API shall be healthy before the frontend window is created. |
| FR-E19-F01-S01-003 | The frontend shall be reachable before the window loads it. |
| FR-E19-F01-S01-004 | The shell shall not spawn a service that is already healthy. |
| FR-E19-F01-S01-005 | The shell shall stop only processes it started. |
| FR-E19-F01-S01-006 | The renderer shall run sandboxed with context isolation and no Node integration. |

## 5. Acceptance Criteria

| AC ID | Acceptance Criteria |
|---|---|
| AC-E19-F01-S01-001 | Given dependencies are ready, when the user starts the desktop app, then search and chart routes appear in Electron. |
| AC-E19-F01-S01-002 | Given the API is unavailable, when Electron starts it, then the window waits until `/health` succeeds. |
| AC-E19-F01-S01-003 | Given API or Next.js is already healthy, when the app starts, then that process is reused. |
| AC-E19-F01-S01-004 | Given a service never becomes healthy, when timeout expires, then owned processes stop and startup fails clearly. |
| AC-E19-F01-S01-005 | Given a seeded symbol is selected, when its chart opens, then history and SSE updates behave as in the browser. |
| AC-E19-F01-S01-006 | Given an external window or navigation request, when it is handled, then the desktop shell denies it. |
| AC-E19-F01-S01-007 | Given the user quits, when shutdown runs, then only shell-owned children are stopped. |

## 6. Test Scenarios

- API command resolution on Windows and POSIX.
- Healthy-service reuse, retry success, timeout, early exit, and idempotent stop.
- Hidden-until-ready window behavior and secure web preferences.
- Same-origin chart window creation and external-origin denial.
- Existing instrument-search, chart, streaming, lint, typecheck, and build regression suites.

## 7. Definition of Done

- All applicable acceptance criteria are automated or manually validated.
- Next.js standalone output builds.
- Local development commands and remaining packaging prerequisites are documented.
- No frontend/backend rewrite or PRD scope expansion is introduced.
