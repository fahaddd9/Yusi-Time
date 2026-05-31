# Database Schema – Yusi Time MVP
**Version:** 2.1 (Changelog — 5 Clockify-Gap Features)
**Date:** 2026-05-26
**Status:** Finalized ✅
**Base Document:** DB Schema v2.0 (Final) — read that document first.
**Aligned with:** PRD v1.3 · TRD v1.2 · API Spec v1.1 · AGENT.md v1.1

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-05-23 | Full schema — 19 tables, all constraints, triggers, DDL |
| 2.1 | 2026-05-26 | **No table or DDL changes.** Section 10 (API↔Table mapping) updated with 3 new endpoints. `saved_report_views.report_type` note updated. Rate resolution note updated for continue/duplicate. |
| 2.2 | 2026-05-31 | **One column added to `users` table.** `is_superadmin BOOLEAN NOT NULL DEFAULT FALSE` added. New Section 12 added documenting Super Admin architecture, bypass strategy, and UI roadmap. No other table, enum, index, or constraint changes. |

---

## IMPORTANT: No Schema Changes Required

All 5 new features from PRD v1.3 are implemented using the **existing schema**
from DB Schema v2.0. No new tables, no new columns, no new enums, no new
indexes, and no migration scripts are required for these features.

Rationale for each feature:

| Feature | Why No Schema Change |
|---------|---------------------|
| Continue entry | Creates a new row in `time_entries` with same FK values. Existing schema covers this exactly. |
| Duplicate entry | Creates a new row in `time_entries` + rows in `time_entry_tags`. Both tables already exist. |
| Description draft | `localStorage` only — never touches the database. |
| Dashboard continue | Reuses `POST /time-entries/start` — no new data structures needed. |
| Weekly report | Aggregates existing `time_entries` rows joined to `users`. No new tables. |
| Super Admin (v2.2) | One boolean column `is_superadmin` added to existing `users` table. No new tables, enums, indexes, or join tables required. The bypass logic lives entirely in the application layer (`dependencies.py`). |

---

## Section 5 — Constraints & Business Rules (Addendum)

### Rate Hierarchy Resolution (Updated — v2.1)

The effective hourly rate for a time entry is resolved by `rate_service.resolve_rate()`
in this priority order:

1. `tasks.hourly_rate_cents` (highest priority)
2. `projects.hourly_rate_cents`
3. `clients.hourly_rate_cents`
4. `workspaces.default_hourly_rate_cents` (lowest priority)

If all are `NULL`, `time_entries.hourly_rate_cents` is stored as `NULL` and
`billable_amount_cents` is `NULL`.

This resolution happens on every save operation: `stop_timer`, `create_manual_entry`,
`update_entry`, **`continue_entry`** (NEW v2.1), and **`duplicate_entry`** (NEW v2.1).

**Critical rule for continue and duplicate:** The new entry created by
`continue_entry` or `duplicate_entry` takes a **fresh rate snapshot** at the
moment of creation. It does NOT inherit `hourly_rate_cents` or
`billable_amount_cents` from the source entry. This is consistent with the
general rule: rate snapshots are always taken at creation time from the current
rate hierarchy state.

### Lock Enforcement Logic (Addendum — v2.1)

The existing lock enforcement table from v2.0 §5 applies unchanged to
continue and duplicate operations:

| Source Entry Status | Continue Permitted? | Duplicate Permitted? |
|---|---|---|
| `draft` | ✅ Yes | ✅ Yes |
| `running` | ✅ Yes (continues the running entry's project/task — new entry starts) | ✅ Yes |
| `pending` | ❌ No — `400 CANNOT_CONTINUE_PENDING` | ❌ No — `400 CANNOT_DUPLICATE_PENDING` |
| `approved` | ✅ Yes | ✅ Yes |
| **Admin role** | Always permitted on any status | Always permitted on any status |

**Why pending is blocked:** A `pending` entry is locked to the member awaiting
approval. Allowing Continue would start a timer implying the work is ongoing —
which contradicts the submitted-for-review state. Allowing Duplicate would create
a new entry whose relationship to the pending submission is ambiguous. Both
operations are blocked at the service layer and return a `400` error code.

### `saved_report_views.report_type` (Clarification — v2.1)

The `saved_report_views.report_type` column is defined as `TEXT NOT NULL`
with a `CHECK (report_type IN ('summary', 'detailed'))` constraint in v2.0.

**This CHECK constraint must be updated** in a migration to allow the new
`'weekly'` value:

```sql
-- Migration: 0002_add_weekly_report_type_to_saved_views.py
-- upgrade():
ALTER TABLE saved_report_views
  DROP CONSTRAINT IF EXISTS saved_report_views_report_type_check;

ALTER TABLE saved_report_views
  ADD CONSTRAINT saved_report_views_report_type_check
  CHECK (report_type IN ('summary', 'detailed', 'weekly'));

-- downgrade():
ALTER TABLE saved_report_views
  DROP CONSTRAINT IF EXISTS saved_report_views_report_type_check;

ALTER TABLE saved_report_views
  ADD CONSTRAINT saved_report_views_report_type_check
  CHECK (report_type IN ('summary', 'detailed'));
```

**This is the only DDL change in v2.1.** It is a constraint-only change —
no column type change, no data migration, no new table.

---

## Section 10 — API Endpoint ↔ Table Mapping (Updated — v2.1)

The following table replaces Section 10 from DB Schema v2.0 in its entirety.
Three new rows marked **NEW** have been added.

| Endpoint Group | Primary Tables |
|----------------|---------------|
| `POST /auth/signup` | `users`, `workspaces`, `workspace_members` |
| `POST /auth/login` | `users` |
| `POST /auth/refresh` | (stateless — JWT only) |
| `POST /auth/forgot-password` | `password_reset_tokens`, `users` |
| `POST /auth/reset-password` | `password_reset_tokens`, `users` |
| `GET/PATCH /users/me` | `users` |
| `DELETE /users/me` | `users` (anonymize), `workspace_members` |
| `GET/POST /workspaces` | `workspaces`, `workspace_members` |
| `PATCH/DELETE /workspaces/{id}` | `workspaces`, `audit_logs` |
| `GET/PATCH/DELETE /workspaces/{id}/members` | `workspace_members`, `audit_logs` |
| `POST/GET/DELETE /workspaces/{id}/invites` | `invites`, `audit_logs` |
| `GET /invites/{token}` | `invites` |
| `POST /invites/{token}/accept` | `invites`, `workspace_members` |
| `GET/POST/PATCH/DELETE /clients` | `clients` |
| `GET/POST/PATCH/DELETE /projects` | `projects`, `project_members`, `tasks` |
| `GET/POST/PATCH/DELETE /tasks` | `tasks` |
| `GET/POST /time-entries` | `time_entries`, `time_entry_tags`, `tags` |
| `GET /time-entries/current` | `time_entries` |
| `POST /time-entries/start` | `time_entries`, `audit_logs` |
| `POST /time-entries/{id}/stop` | `time_entries`, `audit_logs` |
| `POST /time-entries/{id}/continue` | `time_entries`, `time_entry_tags`, `audit_logs` — **NEW v2.1** |
| `POST /time-entries/{id}/duplicate` | `time_entries`, `time_entry_tags`, `audit_logs` — **NEW v2.1** |
| `PATCH/DELETE /time-entries/{id}` | `time_entries`, `time_entry_tags`, `audit_logs` |
| `POST /approvals/submit` | `timesheet_submissions`, `submission_entries`, `time_entries`, `notifications` |
| `GET /approvals/pending` | `timesheet_submissions`, `submission_entries`, `time_entries` |
| `POST /approvals/{id}/approve` | `timesheet_submissions`, `time_entries`, `notifications`, `audit_logs`, `webhook_delivery_logs` |
| `POST /approvals/{id}/reject` | `timesheet_submissions`, `time_entries`, `notifications`, `audit_logs`, `webhook_delivery_logs` |
| `GET /reports/summary` | `time_entries`, `projects`, `clients`, `users` |
| `GET /reports/detailed` | `time_entries`, `projects`, `tasks`, `clients`, `users`, `tags` |
| `GET /reports/weekly` | `time_entries`, `users`, `workspace_members` — **NEW v2.1** |
| `GET /reports/*/export` | Same as above respective report → CSV stream |
| `GET /reports/saved-views` | `saved_report_views` |
| `POST /reports/saved-views` | `saved_report_views` |
| `DELETE /reports/saved-views/{id}` | `saved_report_views` |
| `GET/POST/DELETE /webhooks` | `webhooks` |
| `GET /notifications` | `notifications` |
| `POST /notifications/read` | `notifications` |

---

## Section 11 — Migration & Version Control (Addendum — v2.1)

The migration sequence for Yusi Time MVP is now:

| Migration | File | Changes |
|-----------|------|---------|
| 0001 | `20260523_0900_initial_schema.py` | Full schema from DB Schema v2.0 DDL |
| 0002 | `20260526_1000_add_weekly_report_type.py` | Update `saved_report_views` CHECK constraint to allow `'weekly'` |

Migration 0002 is the **only new migration** required for all 5 new features.
It is a non-destructive constraint change. Existing `saved_report_views` rows
with `report_type = 'summary'` or `report_type = 'detailed'` are unaffected.

---

## Summary of All v2.1 Changes

| Section | Change Type | Description |
|---------|-------------|-------------|
| §5 Rate Resolution | Addendum | continue_entry and duplicate_entry added to save operations that call resolve_rate() |
| §5 Lock Enforcement | Addendum | Table clarifying pending = blocked for both continue and duplicate |
| §5 saved_report_views | DDL change | CHECK constraint updated to include 'weekly' — requires Migration 0002 |
| §10 API↔Table mapping | Row additions | continue, duplicate, and weekly report endpoints added |
| §11 Migration log | Addendum | Migration 0002 documented |

---

## Section 12 — Super Admin Architecture (Added — v2.2)

### Overview

Super Admin is a **platform-level operator account** for Yusi Time founders and
staff. It is implemented as a single boolean flag on the `users` table rather
than as a new workspace role. It exists outside and above the standard
`workspace_role` enum hierarchy.

### Database Change

**Table:** `users`
**Change type:** New column

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `is_superadmin` | `BOOLEAN` | `NOT NULL` | `FALSE` | When `TRUE`, this user is a platform-level operator. Bypasses all workspace membership checks and role-based access controls. Set directly in the database — no UI, no registration flow, no promotion by workspace admins. |

**Alembic migration:** `add_is_superadmin_to_users`
Generate with: `alembic revision --autogenerate -m "add_is_superadmin_to_users"`
Verify the generated script adds exactly: `is_superadmin BOOLEAN NOT NULL DEFAULT FALSE`
Verify `downgrade()` drops the column cleanly.

**Seeding a Super Admin account (direct SQL, no UI):**
```sql
UPDATE users SET is_superadmin = TRUE WHERE email = 'founder@yusitime.com';
```

### Design Principles

1. **Parallel track, not a new role** — `is_superadmin` is entirely separate from
   `workspace_role`. A Super Admin user may simultaneously hold any workspace role
   (admin, manager, member, viewer) or no role at all. The flag overrides the
   workspace role hierarchy completely when `TRUE`.

2. **No workspace membership required** — Super Admins can access any workspace
   endpoint without appearing in `workspace_members`. They bypass the
   `get_workspace_member()` dependency via a synthetic member object (see §12
   Application Layer below).

3. **No UI in current pass** — Super Admin is API-only in the current
   implementation. There is no `/superadmin` route, no admin dashboard, and no
   frontend component. The frontend UI is explicitly deferred to the post-Phase 2
   roadmap (see §12 UI Roadmap below).

4. **No audit logging in current pass** — Audit logging for Super Admin actions
   is deferred to keep scope minimal. Regular `audit_logs` entries will still be
   written for any mutations a Super Admin makes through existing service
   functions, since those functions write audit entries regardless of who calls them.

5. **Database-only assignment** — No existing workspace Admin can promote a user
   to Super Admin. Assignment is exclusively via direct database access by
   platform engineers.

### Application Layer — Bypass Strategy

**File:** `backend/app/core/dependencies.py`

#### `get_workspace_member()` — Synthetic Member Object

When `current_user.is_superadmin is True`, the dependency short-circuits the
`workspace_members` table query entirely and returns a synthetic
`WorkspaceMember` object constructed in memory:

```python
synthetic_member.workspace_id = workspace_id  # from path parameter
synthetic_member.user_id      = current_user.id
synthetic_member.role         = "admin"        # always 'admin' for serialization
```

This synthetic object satisfies the `WorkspaceMember` type contract so that all
downstream routers and response schemas work without modification. Super Admin
always appears as `role='admin'` inside any workspace for the purposes of
response serialization and financial field visibility.

**Why 'admin' and not a new role string:** Using `'admin'` keeps every Pydantic
response schema, every `role != 'viewer'` guard, and every financial field
isolation check completely untouched. Adding a new `'superadmin'` role string
would require updating every schema and every branch — unnecessary complexity
for a flag that already lives outside the role system.

#### `require_role()` — Unconditional Bypass

When `current_user.is_superadmin is True`, the inner `_require_role` dependency
returns the member object immediately without checking `member.role` against the
required roles list. This means Super Admin passes every role gate unconditionally:
`require_role('admin')`, `require_role('manager')`, `require_role('member')` —
all bypassed.

#### `get_superadmin_user()` — New Dedicated Dependency

A new dependency function is added for future Super Admin-only endpoints
(e.g., `GET /admin/workspaces`, `GET /admin/users`). It wraps `get_current_user`
and raises `403 FORBIDDEN` if `is_superadmin` is `FALSE`. Usage:

```python
current_user: User = Depends(get_superadmin_user)
```

This is the correct dependency to use on any endpoint that should be restricted
to platform operators only, as opposed to `require_role('admin')` which applies
to workspace-scoped admin access.

### Affected Files Summary

| File | Change | Scope |
|------|--------|-------|
| `backend/app/models/user.py` | Add `is_superadmin` column | 1 line |
| `backend/app/schemas/user.py` | Add `is_superadmin` field to `UserPublic` | 1 line |
| `backend/app/core/dependencies.py` | Modify `get_workspace_member()`, modify `require_role()`, add `get_superadmin_user()` | ~30 lines |
| `alembic/versions/` | New migration script (generated, not handwritten) | auto-generated |

**Files NOT touched:** All routers, all services, all other models, all schemas,
all frontend files, `app/` directory (post-MVP Flutter placeholder).

### UI Roadmap — Post-Phase 2

The Super Admin Next.js UI ("the VIP Room") is explicitly deferred until after
Phase 2 (Workspace & Member Management) is fully implemented and approved.

**Rationale:** The Super Admin UI is a dashboard for managing workspaces and
their members. Building it before Phase 2 would mean building a management
interface for data structures that do not yet have their full CRUD backend
implemented. After Phase 2, the following will exist and be available for the
Super Admin UI to consume immediately:

- `GET /workspaces` (scoped) → needs a Super Admin variant: `GET /admin/workspaces` (all workspaces)
- `GET /workspaces/{id}` → already accessible via synthetic member bypass
- `GET /workspaces/{id}/members` → already accessible via synthetic member bypass
- `POST /workspaces/{id}/invites` → already accessible via synthetic member bypass

**Planned Super Admin-only endpoints (to be added in the UI phase):**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/workspaces` | List ALL workspaces across the platform (no workspace_id filter) |
| `GET` | `/admin/users` | List ALL users across the platform |
| `PATCH` | `/admin/users/{id}` | Modify any user (e.g., force-reset `is_superadmin`, anonymize) |
| `GET` | `/admin/stats` | Platform-level aggregate stats (total workspaces, users, entries) |

All of the above endpoints will use `Depends(get_superadmin_user)` as their
auth dependency. They will be added to a new router:
`backend/app/routers/admin.py`

**Frontend route:** `/superadmin` (protected by `is_superadmin` flag from
`GET /users/me` response, checked in `middleware.ts`)

**When to build:** After the human supervisor gives explicit written approval
that Phase 2 is COMPLETED and approved. The Super Admin UI phase will be
treated as a named phase in the Implementation Plan at that time.

**Everything else in DB Schema v2.0 is unchanged and remains authoritative.**
