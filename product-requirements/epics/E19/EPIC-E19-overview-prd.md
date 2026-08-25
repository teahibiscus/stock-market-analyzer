# Epic Overview PRD: E19 - Desktop Shell and Workspace

## 1. Document Control

| Field | Value |
|---|---|
| Document Type | Epic Overview PRD |
| Epic ID | E19 |
| Epic Name | Desktop Shell and Workspace |
| Product | Stock Market Charting Application |
| Status | Draft |
| Owner | Product |
| Last Updated | 2026-08-25 |
| Priority / Phase | MVP |
| MVP Scope | Yes |

## 2. Epic Summary

Deliver the application as a secure, desktop-first Electron product while preserving the existing
Next.js UI and FastAPI modular monolith. The shell owns local process lifecycle and provides the
foundation for multi-window, multi-monitor, keyboard-heavy, and saved-workspace workflows.

## 3. Business Objective

Give active traders a low-friction desktop experience without delaying product capabilities through
a frontend or backend rewrite.

## 4. In Scope

- Secure Electron shell for the existing application.
- Local FastAPI and Next.js process startup, health gating, and owned-process shutdown.
- Standalone Next.js production output.
- URL-addressable chart windows and multi-monitor-ready window management.
- Extension points for menus, shortcuts, layouts, notifications, and updates.

## 5. Out of Scope

- Rewriting the React or FastAPI applications.
- Production installer, signing, and update-channel delivery.
- Embedded database replacement, live provider integration, alerts, or AI.
- Full saved-workspace UX beyond URL-addressable window state.

## 6. Features

| Feature ID | Feature Name | Priority |
|---|---|---|
| E19-F01 | Desktop Shell Bootstrap | MVP |

## 7. Functional Requirements

| Requirement ID | Requirement |
|---|---|
| FR-E19-001 | The desktop shell shall load the existing frontend without changing its product behavior. |
| FR-E19-002 | The shell shall start local services and wait for health before displaying the main window. |
| FR-E19-003 | The shell shall stop only child processes that it owns. |
| FR-E19-004 | The shell shall support independent, URL-addressable chart windows. |
| FR-E19-005 | Renderer processes shall not receive direct Node.js access. |

## 8. Non-Functional Requirements

| Requirement ID | Category | Requirement |
|---|---|---|
| NFR-E19-001 | Security | Context isolation and renderer sandboxing shall remain enabled. |
| NFR-E19-002 | Reliability | Startup failure shall not leave owned child processes running. |
| NFR-E19-003 | Performance | A healthy local application should display within 30 seconds. |
| NFR-E19-004 | Compatibility | Windows is the first supported desktop packaging target. |
| NFR-E19-005 | Maintainability | Desktop orchestration shall remain separate from domain modules. |

## 9. Acceptance Criteria

- Search, chart history, and SSE updates behave identically in Electron and the browser.
- One desktop launch starts missing local API and frontend processes after infrastructure is ready.
- External origins cannot open privileged desktop windows.
- Two chart windows can hold independent instrument and timeframe URLs.
- Existing backend and frontend regression suites remain green.

## 10. Dependencies and Risks

- PostgreSQL and Redis remain Docker-managed during the initial desktop phases.
- Python and the backend package remain local prerequisites until packaging bundles a runtime.
- Electron increases memory use; the trade-off is accepted for mature multi-window behavior.
- Code signing, installers, updates, crash recovery, and saved layouts require later E19 features.
