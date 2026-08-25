# Feature PRD: E19-F01 - Desktop Shell Bootstrap

## 1. Document Control

| Field | Value |
|---|---|
| Document Type | Feature PRD |
| Epic ID | E19 |
| Feature ID | E19-F01 |
| Feature Name | Desktop Shell Bootstrap |
| Status | Draft |
| Last Updated | 2026-08-25 |
| Priority / Phase | MVP |
| MVP Scope | Yes |

## 2. Feature Summary

Wrap the existing Next.js application in a hardened Electron shell and manage its local FastAPI and
Next.js services. This feature establishes desktop delivery without moving business logic into
Electron.

## 3. User Value

As an active trader, I can launch the analyzer as one desktop application and retain the search,
chart, and live-update behavior already implemented.

## 4. In Scope

- Hardened main window with context isolation, sandboxing, and no renderer Node integration.
- Health-gated FastAPI and Next.js process lifecycle.
- Reuse of already-running healthy services.
- Next.js standalone output contract.
- Same-origin multi-window foundation using chart URLs.
- Clear startup failure and deterministic shutdown behavior.

## 5. Out of Scope

- Installer and automatic update distribution.
- Bundled Python, PostgreSQL, or Redis runtimes.
- Saved window layouts, native notifications, and production menus.
- Changes to market-data semantics.

## 6. Story

| Story ID | User Story | Priority |
|---|---|---|
| E19-F01-S01 | As an active trader, I want to launch the existing analyzer in a desktop shell so that I can use chart workflows from one application. | MVP |

## 7. Functional Requirements

| Requirement ID | Requirement |
|---|---|
| FR-E19-F01-001 | The shell shall load the configured local frontend URL. |
| FR-E19-F01-002 | The shell shall reuse healthy API or frontend processes rather than starting duplicates. |
| FR-E19-F01-003 | Missing services shall start in API-then-frontend order before a window is shown. |
| FR-E19-F01-004 | Startup shall time out with an actionable diagnostic. |
| FR-E19-F01-005 | Quitting shall stop owned frontend and API child processes. |
| FR-E19-F01-006 | Same-origin chart URLs may open in independent windows; external origins shall be denied. |

## 8. UI and State Requirements

- The main window remains hidden until its content is ready.
- Existing loading, empty, stale, and error states remain owned by the frontend.
- A service startup failure exits cleanly and writes a diagnostic without exposing secrets.
- Chart state remains encoded by instrument, interval, period, and volume query parameters.

## 9. Acceptance Criteria

- Given Docker dependencies are ready, one desktop command starts the missing API and frontend.
- Given either service already responds successfully, no duplicate process is spawned.
- Given startup does not become healthy within its timeout, owned children are stopped.
- Given a renderer requests an external URL, no privileged window is created.
- Given two supported chart URLs, independent desktop windows can load them.
- Existing web use remains supported.

## 10. Test Strategy

- Unit-test launch command resolution, health retries, timeout, ownership, and stop idempotency.
- Unit-test renderer security options and trusted-origin window behavior.
- Build Next.js and assert standalone output exists.
- Run existing frontend, backend foundation, lint, type, and build validation.
