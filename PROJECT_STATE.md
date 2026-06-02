# Yusi Time — Project State
**Last Updated:** 2026-06-01 — Phase 2 Completed
**Current Phase:** Phase 3 — Projects, Tasks, Clients, Tags — ⬜ Not Started
**Last Session Summary:** Phase 2 (Workspace & Members) fully implemented and verified. 101 tests passing, 85.85% coverage, frontend settings UI complete.

---

## Phase Summary Table

| Phase | Name | Status | Date Completed |
|-------|------|--------|----------------|
| 0 | Setup & Infrastructure | ✅ Completed | 2026-05-29 |
| 1 | Authentication | ✅ Completed | 2026-05-31 |
| 1.5 | Super Admin Backend (API-only) | ✅ Completed | 2026-05-31 |
| 2 | Workspace & Members | ✅ Completed | 2026-06-01 |
| 3 | Projects, Tasks, Clients, Tags | ⬜ Not Started | — |
| 4 | Time Tracking Core | ⬜ Not Started | — |
| 5 | Continue, Duplicate & Draft | ⬜ Not Started | — |
| 6 | Approvals & Notifications | ⬜ Not Started | — |
| 7 | Reports & Analytics | ⬜ Not Started | — |
| 7.5 | Super Admin UI Dashboard | ⬜ Not Started | — |
| 8 | Webhooks, Polish & Deploy | ⬜ Not Started | — |

**Status legend:** ⬜ Not Started | 🔄 In Progress | ✅ Completed | ❌ Blocked

---

## Current Phase Detail

### Phase 2 — Workspace & Members — ✅ Completed

#### Steps Completed
- [x] Step 2.1 — Backend Models: Created `Workspace` (updated), `WorkspaceMember` (updated), `Invite`, `AuditLog`, `Notification` models. Generated hand-written migration.
- [x] Step 2.2 — Backend Schemas: Defined validation schemas for all models including `WorkspaceDetailViewer` for financial privacy.
- [x] Step 2.3 — Services: Developed `workspace_service`, `member_service`, `invite_service` (with atomic transactions), `user_service`, and `notification_service`.
- [x] Step 2.4 — Routers: Implemented APIs for `/workspaces`, `/workspaces/{id}/members`, `/workspaces/{id}/invites`, `/invites/{token}` (public), `/users/me`.
- [x] Step 2.5 — Backend Tests: Built unit and integration tests confirming proper role-based access, financial privacy, invite creation/acceptance, and atomic behaviors.
- [x] Step 2.6 — Frontend Stores: Implemented Zustand global stores (`useWorkspaceStore`, `useUIStore`) and a singleton `queryClient` to prevent cache bleed between workspaces.
- [x] Step 2.7 — API + Hooks Layer: Created typed settings API and custom TanStack Query hooks covering all Phase 2 endpoints.
- [x] Step 2.8 — App Layout Shell: Built the authenticated app layout featuring the global `Sidebar`, `WorkspaceSwitcher`, user profile fetching, and token refresh handling.
- [x] Step 2.9 — Settings Pages: Developed Workspace settings (H1-H4), Members settings (H4), and Profile settings with full role-based feature gating.
- [x] Step 2.10 — Invite Flow: Implemented the public invite acceptance page (`/join/[token]`) with intelligent redirection for unauthenticated users.

#### Steps In Progress
*(None)*

#### Steps Remaining
*(None)*

#### Decisions Made
- Skipped Alembic autogenerate because it detected future tables as "removed" (Phase 1 DB schema was already complete for the whole app).
- Created a singleton `queryClient` to allow the `useWorkspaceStore` to cleanly clear all caches (`queryClient.clear()`) on workspace switch.
- Notification model renamed `metadata` column to `event_metadata` to avoid conflicts with SQLAlchemy's internal `DeclarativeBase.metadata`.
- The invite acceptance flow intelligently routes users through login/signup if they don't have an active token, preserving the invite token in the URL.

#### Issues / Bugs Discovered and Resolved
- SQLAlchemy reserved keyword collision on `Notification.metadata` → renamed to `event_metadata`.
- Two integration tests encountered datetime fixture drift → resolved by using `freezegun` / standardizing test fixture times.
- Pytest threw `coroutine was never awaited` warnings in tests → resolved by correctly awaiting async DB insertions.

#### Open Blockers
*(None)*

#### Test Results
- `pytest tests/ -v`: **101 passed, 0 failed**
- `pytest --cov=app --cov-fail-under=80`: **85.85% coverage ✅**

#### Phase 2 Completion Status
100% complete. All tests passing. All checklist items verified.
Human supervisor approval received: Pending

---

## Future Enhancements (Post-MVP Backlog)

*(Items logged here when human supervisor approves moving them out of MVP scope)*

| Date | Requested Feature | Why Out of Scope | Logged By |
|------|------------------|-----------------|-----------| 
| — | — | — | — |

---

## Architecture Decisions Log

*(Record any significant implementation decisions here for future reference)*

| Date | Decision | Rationale | Document Reference |
|------|----------|-----------|-------------------|
| 2026-05-26 | DB Schema v2.1 — saved_report_views CHECK constraint includes 'weekly' | Required by new Weekly Report feature (PRD v1.3 §3.8) | DB Schema v2.1 §5 |
| 2026-05-26 | Continue/Duplicate return null in UI for pending entries (not disabled) | Prevents ambiguous interaction with entries under review | PRD v1.3 §7 · Blueprint v2.0 §11 |
| 2026-05-26 | Rate snapshot is always fresh on continue/duplicate (never inherited) | Prevents stale rate data propagating into new entries | PRD v1.3 §5 · TRD v1.2 §6.6 |
| 2026-05-31 | Synthetic WorkspaceMember written via `__dict__` not attribute assignment | SQLAlchemy class-level descriptors intercept both direct assignment and object.__setattr__; __dict__ bypass is the only descriptor-safe approach | Phase 1.5 implementation |
| 2026-05-31 | Hand-written Alembic migration for is_superadmin column | Autogenerate detects Phase 2+ tables (in DB but not yet in models) as "removed"; targeted migration is required to avoid data loss | Phase 1.5 implementation |
