# Database Schema – Yusi Time MVP
**Version:** 2.0 (Final — Expert Review & Full Enhancement)
**Date:** 2026-05-23
**Status:** Finalized ✅
**Aligned with:** PRD v1.2 (Final) · TRD v1.1 (Final) · AGENT.md v1.1 (Final)
**Author:** YusiTime Architect (DB Expert Review)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-23 | Initial draft (DeepSeek generated) |
| 2.0 | 2026-05-23 | Full expert review and rewrite: 18 issues resolved; 4 new tables added (`password_reset_tokens`, `saved_report_views`, `audit_logs`, `webhook_delivery_logs`); `entry_status` enum corrected; `webhook_event_type` and `notification_event_type` enums added; `tasks.workspace_id` added; `submission_entries` unique constraint fixed; `timesheet_submissions` double-submit guard added; `project_members` audit columns added; `clients` unique constraint formalized; `invites.role` guard added; all monetary columns reviewed for overflow; `updated_at` trigger strategy documented; complete SQL DDL appendix added |

---

## Table of Contents
1. [Entity-Relationship Overview](#1-entity-relationship-overview)
2. [Design Principles](#2-design-principles)
3. [Enum Definitions](#3-enum-definitions)
4. [Table Definitions](#4-table-definitions)
   - [4.1 `users`](#41-users)
   - [4.2 `password_reset_tokens`](#42-password_reset_tokens)
   - [4.3 `workspaces`](#43-workspaces)
   - [4.4 `workspace_members`](#44-workspace_members)
   - [4.5 `invites`](#45-invites)
   - [4.6 `clients`](#46-clients)
   - [4.7 `projects`](#47-projects)
   - [4.8 `project_members`](#48-project_members)
   - [4.9 `tasks`](#49-tasks)
   - [4.10 `tags`](#410-tags)
   - [4.11 `time_entries`](#411-time_entries)
   - [4.12 `time_entry_tags`](#412-time_entry_tags)
   - [4.13 `timesheet_submissions`](#413-timesheet_submissions)
   - [4.14 `submission_entries`](#414-submission_entries)
   - [4.15 `saved_report_views`](#415-saved_report_views)
   - [4.16 `webhooks`](#416-webhooks)
   - [4.17 `webhook_delivery_logs`](#417-webhook_delivery_logs)
   - [4.18 `notifications`](#418-notifications)
   - [4.19 `audit_logs`](#419-audit_logs)
5. [Constraints & Business Rules](#5-constraints--business-rules)
6. [Indexes](#6-indexes)
7. [Triggers](#7-triggers)
8. [Cascading & Referential Actions](#8-cascading--referential-actions)
9. [Monetary Storage Convention](#9-monetary-storage-convention)
10. [API Endpoint ↔ Table Mapping](#10-api-endpoint--table-mapping)
11. [Migration & Version Control](#11-migration--version-control)
12. [Appendix A — Full SQL DDL](#12-appendix-a--full-sql-ddl)

---

## 1. Entity-Relationship Overview

```
users
 ├── password_reset_tokens          (user_id FK)
 ├── workspace_members              (user_id, workspace_id FK)
 ├── audit_logs                     (actor_user_id FK)
 │
 └── workspaces
      ├── workspace_members          (workspace_id FK)
      ├── invites                    (workspace_id, created_by_user_id FK)
      ├── clients
      │    └── projects              (client_id FK, nullable)
      │         ├── project_members  (project_id, user_id FK)
      │         └── tasks            (project_id FK)
      │              └── time_entries (task_id FK, nullable)
      │
      ├── tags
      │    └── time_entry_tags       (tag_id, time_entry_id FK)
      │
      ├── time_entries               (workspace_id, user_id, project_id FK)
      │    └── submission_entries    (time_entry_id FK)
      │         └── timesheet_submissions (workspace_id, user_id FK)
      │
      ├── saved_report_views         (workspace_id, user_id FK)
      │
      ├── webhooks                   (workspace_id FK)
      │    └── webhook_delivery_logs (webhook_id FK)
      │
      └── notifications              (workspace_id, user_id FK)
```

All workspace-scoped tables carry a `workspace_id` column and cascade on hard workspace deletion (triggered 30 days after soft-delete per PRD §3.1).

---

## 2. Design Principles

These principles govern every decision in this schema:

1. **UUID v4 primary keys** on all tables. Generated via `gen_random_uuid()` (pgcrypto extension). No sequential integers — UUIDs prevent enumeration attacks and are safe for distributed systems.
2. **All timestamps with timezone** (`TIMESTAMPTZ`). Stored and returned in UTC. The `default_timezone` on the workspace and the user's `timezone` override are display-only — the database never converts timestamps.
3. **Monetary values in integer cents** (`BIGINT`). No `FLOAT` or `NUMERIC` for money. Cents avoid floating-point precision errors. All monetary columns use the `_cents` suffix. See §9 for the full convention.
4. **Soft delete via `deleted_at`** on the `workspaces` table. Hard deletion of workspace data occurs 30 days after `deleted_at` is set (via a scheduled job, not a DB trigger). All other entities use hard deletion cascading from the workspace.
5. **Anonymization in place** on `users`. The user record is mutated rather than deleted to preserve referential integrity across all linked time entries, submissions, and audit logs.
6. **Enums for all categorical columns**. Using PostgreSQL native `CREATE TYPE ... AS ENUM` for all status, role, and mode columns. This enforces valid values at the database layer, not just the application layer.
7. **Partial unique indexes** to enforce singleton business rules (e.g., one running timer per user per workspace).
8. **`updated_at` maintained by triggers**, not by application code — prevents any update path (direct SQL, migration, admin tool) from leaving a stale timestamp.
9. **Audit log for all sensitive mutations**. A dedicated `audit_logs` table captures who changed what and when across all security-relevant entities.
10. **Foreign keys on every relationship** with explicit `ON DELETE` actions documented and justified.

---

## 3. Enum Definitions

All enums are created as PostgreSQL native types.

| Enum Name | Values | Used In |
|-----------|--------|---------|
| `workspace_role` | `admin`, `manager`, `member`, `viewer` | `workspace_members.role`, `invites.role` |
| `project_visibility` | `public`, `private` | `projects.visibility` |
| `project_status` | `active`, `archived` | `projects.status` |
| `entry_status` | `draft`, `running`, `pending`, `approved` | `time_entries.status` |
| `submission_status` | `pending`, `approved`, `rejected` | `timesheet_submissions.status` |
| `rounding_mode` | `none`, `nearest`, `up`, `down` | `workspaces.rounding_mode` |
| `webhook_event_type` | `time_entry.created`, `time_entry.updated`, `timesheet.submitted`, `timesheet.approved`, `timesheet.rejected` | `webhook_delivery_logs.event_type`, `webhooks` subscription filter |
| `notification_event_type` | `timesheet_submitted`, `timesheet_approved`, `timesheet_rejected`, `timer_auto_stopped`, `workspace_deleted` | `notifications.event_type` |
| `audit_action` | `create`, `update`, `delete`, `approve`, `reject`, `submit`, `lock_override`, `role_change`, `invite_generated`, `invite_revoked`, `workspace_soft_deleted` | `audit_logs.action` |
| `webhook_delivery_status` | `success`, `failed`, `retrying` | `webhook_delivery_logs.status` |

**Important correction from v1.0**: The `entry_status` enum **does not include `rejected`**. Time entries are never individually rejected — only a `timesheet_submission` is rejected. When a submission is rejected, its linked entries revert from `pending` back to `draft`. This aligns with PRD v1.2 §3.6.2: "All entries in that submission revert to Unlocked/Editable status." The `rejected` value has been removed from `entry_status` and correctly belongs only on `submission_status`.

---

## 4. Table Definitions

---

### 4.1 `users`

Core identity table. User records are **anonymized in-place** upon account deletion (PRD §3.1). The record is never hard-deleted; referential integrity for time entries and audit logs is preserved.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | Immutable user identifier |
| `email` | `TEXT` | `UNIQUE NOT NULL` | — | Stored lowercase. On anonymization: set to `deleted-{short-uuid}@anonymous.local` |
| `password_hash` | `TEXT` | `NULL` | `NULL` | Argon2 hash. `NULL` for Google-only accounts |
| `google_id` | `TEXT` | `UNIQUE NULL` | `NULL` | Google OAuth subject (`sub`). Set to `NULL` on anonymization |
| `full_name` | `TEXT` | `NOT NULL` | — | Display name. On anonymization: set to `Deleted User {short-uuid}` |
| `avatar_url` | `TEXT` | `NULL` | `NULL` | User-provided profile photo URL |
| `timezone` | `TEXT` | `NULL` | `NULL` | IANA timezone string (e.g., `America/New_York`). Overrides workspace timezone for display |
| `weekly_hours_goal` | `SMALLINT` | `NULL CHECK (weekly_hours_goal > 0)` | `NULL` | Personal weekly target in hours |
| `is_active` | `BOOLEAN` | `NOT NULL` | `TRUE` | Set to `FALSE` on anonymization. Anonymized accounts cannot log in |
| `is_superadmin` | `BOOLEAN` | `NOT NULL` | `FALSE` | Platform-level operator flag. When `TRUE`, bypasses all workspace membership checks and role-based access controls. Set directly in the database only — no UI or promotion flow. See DB Schema v2.2 Changelog §12 for full architecture. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Business rules:**
- Email is stored and compared case-insensitively. Use a `LOWER(email)` functional index.
- A user cannot delete their account if they are the sole `admin` in any non-deleted workspace. This is enforced in `auth_service.py`, not at the DB level.
- `google_id` has a UNIQUE constraint to prevent two accounts linking to the same Google identity.
- `is_superadmin` is set exclusively via direct database access by platform engineers. No application endpoint, no admin UI, and no workspace Admin role can set this flag. Defaults to `FALSE` for all new users including those created via `POST /auth/signup` and Google OAuth.

---

### 4.2 `password_reset_tokens`

Stores secure, time-limited tokens for the password reset flow. This is the only email flow in MVP (PRD §3.2).

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE CASCADE` | — | The user requesting the reset |
| `token` | `TEXT` | `UNIQUE NOT NULL` | — | `secrets.token_urlsafe(32)`. Never stored in plain text in logs |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW() + interval '1 hour'` | Per PRD §3.2: links expire in 1 hour |
| `used` | `BOOLEAN` | `NOT NULL` | `FALSE` | Set `TRUE` immediately on successful password reset |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |

**Business rules:**
- A new reset request invalidates all prior unused tokens for the same user (enforced in `auth_service.py` by deleting previous rows before inserting).
- Expired and used tokens are inert. A scheduled cleanup job (or Alembic migration utility) can purge rows older than 24 hours.
- `CHECK (expires_at > created_at)`.

---

### 4.3 `workspaces`

Tenant container. Every workspace-scoped table references this via `workspace_id`. Soft-deleted via `deleted_at`; all data hard-deleted 30 days after soft-deletion.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `name` | `TEXT` | `NOT NULL` | — | Workspace display name |
| `logo_url` | `TEXT` | `NULL` | `NULL` | Optional logo image URL |
| `default_timezone` | `TEXT` | `NOT NULL` | `'UTC'` | IANA timezone. Display only — DB stores UTC |
| `date_format` | `TEXT` | `NOT NULL CHECK (date_format IN ('MM/DD/YYYY','DD/MM/YYYY'))` | `'MM/DD/YYYY'` | Display format for dates in the UI |
| `currency` | `CHAR(3)` | `NOT NULL` | `'USD'` | ISO 4217 currency code (3 characters) |
| `default_hourly_rate_cents` | `BIGINT` | `NULL CHECK (default_hourly_rate_cents >= 0)` | `NULL` | Workspace-level default hourly rate in cents |
| `rounding_mode` | `rounding_mode` | `NOT NULL` | `'none'` | One of the `rounding_mode` enum values |
| `rounding_interval_minutes` | `SMALLINT` | `NULL CHECK (rounding_interval_minutes IN (1,5,6,10,15,30))` | `NULL` | Required when `rounding_mode != 'none'`; enforced by application + DB check below |
| `mandatory_description` | `BOOLEAN` | `NOT NULL` | `FALSE` | Requires `description` on every time entry |
| `max_timer_duration_seconds` | `INTEGER` | `NOT NULL CHECK (max_timer_duration_seconds > 0)` | `86400` | 24h default. Auto-stops timer when exceeded |
| `past_entry_limit_days` | `SMALLINT` | `NOT NULL CHECK (past_entry_limit_days >= 0)` | `7` | How many days back a manual entry can be backdated |
| `lock_period_days` | `SMALLINT` | `NOT NULL CHECK (lock_period_days >= 0)` | `7` | Rolling lock window in days. `0` = no locking |
| `approval_workflow_enabled` | `BOOLEAN` | `NOT NULL` | `FALSE` | Enables the submit/approve/reject workflow |
| `idle_detection_enabled` | `BOOLEAN` | `NOT NULL` | `FALSE` | Enables per-device idle detection |
| `idle_timeout_minutes` | `SMALLINT` | `NULL CHECK (idle_timeout_minutes IN (1,2,5,10,15))` | `NULL` | Required when `idle_detection_enabled = TRUE` |
| `deleted_at` | `TIMESTAMPTZ` | `NULL` | `NULL` | Soft-delete marker. Set by Admin. Hard deletion by scheduled job after 30 days |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Composite CHECK constraints:**
```sql
-- Rounding interval must be set when mode is not 'none'
CHECK (
  rounding_mode = 'none'
  OR (rounding_mode != 'none' AND rounding_interval_minutes IS NOT NULL)
)

-- Idle timeout must be set when idle detection is enabled
CHECK (
  idle_detection_enabled = FALSE
  OR (idle_detection_enabled = TRUE AND idle_timeout_minutes IS NOT NULL)
)
```

---

### 4.4 `workspace_members`

Junction table linking users to workspaces with a role. Composite primary key prevents duplicate memberships.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE RESTRICT` | — | RESTRICT: remove membership before deleting (anonymization) |
| `role` | `workspace_role` | `NOT NULL` | `'member'` | Current role of this user in this workspace |
| `joined_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | When the user joined (accepted invite or was the creator) |
| `invited_by_user_id` | `UUID` | `NULL FK → users(id) ON DELETE SET NULL` | `NULL` | Admin who invited this member. `NULL` for the workspace creator |
| **PRIMARY KEY** | `(workspace_id, user_id)` | — | — | Prevents duplicate membership |

**Business rule:** Only one `admin` role is required per workspace (the creator). Multiple admins are allowed. The application must prevent the removal of the last admin.

---

### 4.5 `invites`

Stores generated invite links per workspace. Only Admins can create these (PRD §3.1). Links are single-use, expire in 7 days, and can be revoked.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `email` | `TEXT` | `NOT NULL` | — | The email address the invite was intended for. For record-keeping only — no email is sent in MVP |
| `role` | `workspace_role` | `NOT NULL CHECK (role IN ('manager','member','viewer'))` | `'member'` | Pre-assigned role. Admins cannot be invited — they must be promoted from within |
| `token` | `TEXT` | `UNIQUE NOT NULL` | — | `secrets.token_urlsafe(32)`. URL-safe base64 token |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW() + interval '7 days'` | Hardcoded 7-day expiry per PRD §3.1 |
| `used` | `BOOLEAN` | `NOT NULL` | `FALSE` | Set `TRUE` on successful `accept_invite` |
| `used_by_user_id` | `UUID` | `NULL FK → users(id) ON DELETE SET NULL` | `NULL` | The user who consumed this invite |
| `used_at` | `TIMESTAMPTZ` | `NULL` | `NULL` | When the invite was accepted |
| `revoked` | `BOOLEAN` | `NOT NULL` | `FALSE` | Admin manually revokes before use |
| `revoked_at` | `TIMESTAMPTZ` | `NULL` | `NULL` | When the invite was revoked |
| `created_by_user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE RESTRICT` | — | The Admin who generated this invite |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |

**Constraints:**
```sql
CHECK (expires_at > created_at)
-- role cannot be 'admin' (enforced by the CHECK on role values above)
-- Consistency: used and used_at must both be set together
CHECK ( (used = TRUE AND used_at IS NOT NULL) OR (used = FALSE AND used_at IS NULL) )
-- Consistency: revoked and revoked_at must both be set together
CHECK ( (revoked = TRUE AND revoked_at IS NOT NULL) OR (revoked = FALSE AND revoked_at IS NULL) )
-- An invite cannot be both used and revoked
CHECK (NOT (used = TRUE AND revoked = TRUE))
```

---

### 4.6 `clients`

Optional grouping entity for projects. Purely organizational — no functional logic beyond rate inheritance and reporting.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `name` | `TEXT` | `NOT NULL` | — | Client display name |
| `email` | `TEXT` | `NULL` | `NULL` | Optional contact email. For reference only |
| `phone` | `TEXT` | `NULL` | `NULL` | Optional contact phone. For reference only |
| `hourly_rate_cents` | `BIGINT` | `NULL CHECK (hourly_rate_cents >= 0)` | `NULL` | Client-level default rate. Overrides workspace rate |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Unique constraint:**
```sql
UNIQUE (workspace_id, name)
-- Client names must be unique within a workspace
```

---

### 4.7 `projects`

Core project entity. Visibility controls which members can see and log time on it.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `client_id` | `UUID` | `NULL FK → clients(id) ON DELETE SET NULL` | `NULL` | Optional client. `NULL` if project has no client |
| `name` | `TEXT` | `NOT NULL` | — | Project display name |
| `default_billable` | `BOOLEAN` | `NOT NULL` | `TRUE` | Default billable flag for new time entries on this project |
| `budget_hours` | `NUMERIC(10,2)` | `NULL CHECK (budget_hours > 0)` | `NULL` | Budget in hours. Triggers 80%/100% warnings |
| `budget_amount_cents` | `BIGINT` | `NULL CHECK (budget_amount_cents > 0)` | `NULL` | Budget in cents. Alternative to `budget_hours`; both can be set simultaneously |
| `visibility` | `project_visibility` | `NOT NULL` | `'public'` | `public`: visible to all members. `private`: visible only to assigned members + Managers + Admins |
| `status` | `project_status` | `NOT NULL` | `'active'` | `archived` projects hidden from timer dropdowns but visible in reports |
| `hourly_rate_cents` | `BIGINT` | `NULL CHECK (hourly_rate_cents >= 0)` | `NULL` | Project-level rate. Overrides client rate |
| `color` | `CHAR(7)` | `NULL CHECK (color ~ '^#[0-9A-Fa-f]{6}$')` | `NULL` | Optional hex color code for UI differentiation (e.g., `#3B82F6`) |
| `archived_at` | `TIMESTAMPTZ` | `NULL` | `NULL` | Set when `status` transitions to `archived` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Unique constraint:**
```sql
UNIQUE (workspace_id, name)
-- Project names must be unique within a workspace
```

**Consistency constraint:**
```sql
CHECK (
  (status = 'archived' AND archived_at IS NOT NULL)
  OR (status = 'active' AND archived_at IS NULL)
)
```

---

### 4.8 `project_members`

Explicit member assignments for private projects. Managers and Admins always have access to all projects regardless of this table.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `project_id` | `UUID` | `NOT NULL FK → projects(id) ON DELETE CASCADE` | — | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE RESTRICT` | — | — |
| `added_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | When this member was assigned to the project |
| `added_by_user_id` | `UUID` | `NULL FK → users(id) ON DELETE SET NULL` | `NULL` | Manager/Admin who made the assignment |
| **PRIMARY KEY** | `(project_id, user_id)` | — | — | Prevents duplicate assignment |

---

### 4.9 `tasks`

Optional sub-entities within a project. Tasks inherit the project's billable flag unless `billable_override` is set.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | Denormalized for efficient workspace-scoped queries without joining through projects |
| `project_id` | `UUID` | `NOT NULL FK → projects(id) ON DELETE CASCADE` | — | — |
| `name` | `TEXT` | `NOT NULL` | — | Task display name |
| `assignee_user_id` | `UUID` | `NULL FK → users(id) ON DELETE SET NULL` | `NULL` | Single workspace member assigned to this task |
| `estimated_hours` | `NUMERIC(8,2)` | `NULL CHECK (estimated_hours > 0)` | `NULL` | Estimated effort in hours |
| `billable_override` | `BOOLEAN` | `NULL` | `NULL` | `NULL` = inherit from project. `TRUE`/`FALSE` = override |
| `hourly_rate_cents` | `BIGINT` | `NULL CHECK (hourly_rate_cents >= 0)` | `NULL` | Task-level rate. Highest priority in rate hierarchy |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Unique constraint:**
```sql
UNIQUE (project_id, name)
-- Task names must be unique within a project
```

**Why `workspace_id` on tasks?** Without it, every query for "all tasks in workspace X" requires a JOIN through `projects`. Adding `workspace_id` directly on `tasks` (denormalized) enables efficient filtering and is consistent with the TRD index requirement. A trigger or application constraint ensures `tasks.workspace_id = projects.workspace_id`.

---

### 4.10 `tags`

Reusable labels applied to individual time entries. Managed at workspace level.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `name` | `TEXT` | `NOT NULL` | — | Tag label |
| `color` | `CHAR(7)` | `NULL CHECK (color ~ '^#[0-9A-Fa-f]{6}$')` | `NULL` | Optional hex color for UI display |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |

**Unique constraint:**
```sql
UNIQUE (workspace_id, name)
-- Tag names must be unique within a workspace
```

---

### 4.11 `time_entries`

The core time tracking record. Status drives all locking, approval, and editability rules.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE RESTRICT` | — | The member who logged this time |
| `project_id` | `UUID` | `NOT NULL FK → projects(id) ON DELETE RESTRICT` | — | RESTRICT: archive projects instead of deleting if entries exist |
| `task_id` | `UUID` | `NULL FK → tasks(id) ON DELETE SET NULL` | `NULL` | Optional task. SET NULL if task deleted |
| `description` | `TEXT` | `NULL` | `NULL` | Free-form work notes. Required if `workspaces.mandatory_description = TRUE` (enforced in application) |
| `billable` | `BOOLEAN` | `NOT NULL` | `TRUE` | Inherited from task or project default at creation time |
| `status` | `entry_status` | `NOT NULL` | `'draft'` | `draft` = editable. `running` = active timer. `pending` = submitted awaiting approval. `approved` = locked |
| `start_time` | `TIMESTAMPTZ` | `NOT NULL` | — | Timer start time. For manual entries: user-provided start |
| `end_time` | `TIMESTAMPTZ` | `NULL` | `NULL` | `NULL` when `status = 'running'`. Populated on stop or for manual entries |
| `duration_seconds` | `INTEGER` | `NULL CHECK (duration_seconds >= 0)` | `NULL` | **Rounded** duration in seconds. Stored on stop/create/edit. Never stores raw seconds (PRD §3.3.4) |
| `hourly_rate_cents` | `BIGINT` | `NULL CHECK (hourly_rate_cents >= 0)` | `NULL` | **Snapshot** of effective rate at moment of save. Immutable after write |
| `billable_amount_cents` | `BIGINT` | `NULL CHECK (billable_amount_cents >= 0)` | `NULL` | Computed and stored: `ROUND((duration_seconds / 3600.0) * hourly_rate_cents)`. Stored, not computed on-the-fly, to avoid re-computation drift |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**CHECK constraints:**
```sql
-- End time must be after start time when both are present
CHECK (end_time IS NULL OR end_time > start_time)

-- Running entries must not have an end_time or duration
CHECK (
  status != 'running'
  OR (status = 'running' AND end_time IS NULL AND duration_seconds IS NULL)
)

-- Completed entries must have both end_time and duration_seconds
CHECK (
  status = 'running' OR status = 'draft'
  OR (end_time IS NOT NULL AND duration_seconds IS NOT NULL)
)
```

**Business rules enforced at application layer:**
- Overlapping entries are permitted. No DB exclusion constraint.
- `mandatory_description` check (workspace setting) enforced in `time_entry_service.py`.
- Lock-date enforcement (member cannot edit entries older than `workspace.lock_period_days` when status is `approved`) enforced in `time_entry_service.update_entry()`.
- Past-entry limit (`workspace.past_entry_limit_days`) enforced in `time_entry_service.create_manual_entry()`.

**Why `BIGINT` for `billable_amount_cents`?** An `INTEGER` in PostgreSQL stores up to ~2.1 billion, which is $21 million per entry. For most teams this is sufficient, but using `BIGINT` (max ~9.2 quintillion) costs nothing extra in PostgreSQL storage for this column and eliminates any overflow risk for high-rate, long-duration entries. Consistent with all other monetary columns.

---

### 4.12 `time_entry_tags`

Many-to-many join table between time entries and tags.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `time_entry_id` | `UUID` | `NOT NULL FK → time_entries(id) ON DELETE CASCADE` | — | — |
| `tag_id` | `UUID` | `NOT NULL FK → tags(id) ON DELETE CASCADE` | — | — |
| **PRIMARY KEY** | `(time_entry_id, tag_id)` | — | — | Prevents duplicate tag assignments |

---

### 4.13 `timesheet_submissions`

Tracks each "Submit Week" action by a user. Links to the submitted entries via `submission_entries`.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE RESTRICT` | — | Member who submitted |
| `week_start` | `DATE` | `NOT NULL` | — | Always a Monday. The start of the Mon–Sun week being submitted |
| `status` | `submission_status` | `NOT NULL` | `'pending'` | `pending` → `approved` or `rejected` |
| `submitted_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `reviewed_by_user_id` | `UUID` | `NULL FK → users(id) ON DELETE SET NULL` | `NULL` | Manager or Admin who approved/rejected |
| `reviewed_at` | `TIMESTAMPTZ` | `NULL` | `NULL` | When the review action was taken |
| `rejection_note` | `TEXT` | `NULL` | `NULL` | Mandatory when `status = 'rejected'`. Enforced by CHECK below |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**CHECK constraints:**
```sql
-- week_start must always be a Monday (DOW = 1 in PostgreSQL where Sunday = 0)
CHECK (EXTRACT(DOW FROM week_start) = 1)

-- rejection_note is mandatory when status is rejected
CHECK (
  status != 'rejected'
  OR (status = 'rejected' AND rejection_note IS NOT NULL AND TRIM(rejection_note) != '')
)

-- reviewed_at must be set when a review action has occurred
CHECK (
  (status = 'pending' AND reviewed_at IS NULL)
  OR (status != 'pending' AND reviewed_at IS NOT NULL)
)
```

**Partial unique index** to prevent double-submission:
```sql
-- A user can have at most one PENDING submission per week per workspace
CREATE UNIQUE INDEX uq_timesheet_submissions_one_pending
ON timesheet_submissions (workspace_id, user_id, week_start)
WHERE status = 'pending';
```
This allows re-submission after rejection (since rejected submissions are no longer `pending`) while preventing accidental double-clicks from creating two pending submissions.

---

### 4.14 `submission_entries`

Join table linking submitted time entries to a timesheet submission. Provides the historical record of what was included in each submission, even after entries are approved or rejected.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `submission_id` | `UUID` | `NOT NULL FK → timesheet_submissions(id) ON DELETE CASCADE` | — | — |
| `time_entry_id` | `UUID` | `NOT NULL FK → time_entries(id) ON DELETE CASCADE` | — | — |
| **PRIMARY KEY** | `(submission_id, time_entry_id)` | — | — | Prevents duplicate rows in the join |

**Critical additional constraint:**
```sql
-- An entry can belong to at most ONE submission at any point in time.
-- Without this, the same entry could appear in two different submissions simultaneously.
CREATE UNIQUE INDEX uq_submission_entries_one_submission_per_entry
ON submission_entries (time_entry_id);
```
The composite PK only prevents the same `(submission_id, time_entry_id)` pair from appearing twice. The unique index on `time_entry_id` alone prevents the same entry from being in two different submissions. When a submission is rejected and entries revert to `draft`, the old `submission_entries` rows remain as history; a new submission creates new rows.

---

### 4.15 `saved_report_views`

Stores users' saved filter configurations for reports. Per PRD §3.8: private to the user's account.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE CASCADE` | — | Owner of this saved view. CASCADE: delete views when user account is deleted/anonymized |
| `name` | `TEXT` | `NOT NULL` | — | User-provided name for this saved view |
| `report_type` | `TEXT` | `NOT NULL CHECK (report_type IN ('summary', 'detailed'))` | — | Which report this view applies to |
| `filters` | `JSONB` | `NOT NULL` | `'{}'` | Serialized filter state: date range, project_ids, user_ids, client_ids, billable flag, tags, grouping |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Unique constraint:**
```sql
UNIQUE (workspace_id, user_id, name)
-- A user cannot have two saved views with the same name in the same workspace
```

**`filters` JSONB structure example:**
```json
{
  "date_from": "2026-05-01",
  "date_to": "2026-05-31",
  "project_ids": ["uuid1", "uuid2"],
  "user_ids": [],
  "client_ids": [],
  "billable": null,
  "tag_ids": [],
  "group_by": "project"
}
```

---

### 4.16 `webhooks`

Registered webhook endpoints per workspace. Admin-only management.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `url` | `TEXT` | `NOT NULL` | — | Target HTTPS URL to POST events to |
| `secret` | `TEXT` | `NULL` | `NULL` | HMAC-SHA256 signing secret. If set, the backend signs every payload with `X-Yusitime-Signature` |
| `subscribed_events` | `webhook_event_type[]` | `NOT NULL` | — | PostgreSQL array of `webhook_event_type` enum values this webhook subscribes to |
| `is_active` | `BOOLEAN` | `NOT NULL` | `TRUE` | Admin can temporarily disable without deleting |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | Maintained by trigger |

**Design note:** Using a PostgreSQL native array (`webhook_event_type[]`) for `subscribed_events` instead of the separate `webhook_events` join table from v1.0. This is cleaner for this use case: the subscriptions are always read and written together with the webhook record, they have no independent lifecycle, and there is no query that needs to find "all webhooks subscribed to event X" without also needing the webhook URL. The array approach reduces a JOIN on every dispatch.

**CHECK constraint:**
```sql
CHECK (url LIKE 'https://%')
-- Only HTTPS webhook URLs are accepted
```

---

### 4.17 `webhook_delivery_logs`

Persists every webhook delivery attempt including retries. Required by TRD §6.7: failures are logged at ERROR level after 3 retry exhaustion. This table provides the persistent audit trail.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `webhook_id` | `UUID` | `NOT NULL FK → webhooks(id) ON DELETE CASCADE` | — | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | Denormalized for efficient workspace-scoped queries |
| `event_type` | `webhook_event_type` | `NOT NULL` | — | The event that triggered this delivery |
| `payload` | `JSONB` | `NOT NULL` | — | The exact JSON body that was sent (or attempted) |
| `attempt_number` | `SMALLINT` | `NOT NULL CHECK (attempt_number BETWEEN 1 AND 3)` | `1` | 1 = first attempt, 2 = first retry, 3 = second retry |
| `status` | `webhook_delivery_status` | `NOT NULL` | `'retrying'` | `success`, `failed`, `retrying` |
| `http_status_code` | `SMALLINT` | `NULL` | `NULL` | HTTP response code from the target. `NULL` if connection failed (timeout, DNS error) |
| `response_body` | `TEXT` | `NULL` | `NULL` | First 1000 characters of the response body for debugging |
| `error_message` | `TEXT` | `NULL` | `NULL` | Error description if delivery failed (timeout message, connection refused, etc.) |
| `attempted_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | When this specific attempt was made |

**Index:**
```sql
CREATE INDEX ix_webhook_delivery_logs_webhook_attempted
ON webhook_delivery_logs (webhook_id, attempted_at DESC);
-- Supports "show recent deliveries for this webhook" queries
```

---

### 4.18 `notifications`

In-app notification center. Workspace-scoped per user. Per PRD §3.10.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NOT NULL FK → workspaces(id) ON DELETE CASCADE` | — | — |
| `user_id` | `UUID` | `NOT NULL FK → users(id) ON DELETE CASCADE` | — | Recipient. CASCADE: remove notifications if user is hard-deleted (not applicable for anonymized users) |
| `event_type` | `notification_event_type` | `NOT NULL` | — | Typed enum for the triggering event |
| `title` | `TEXT` | `NOT NULL` | — | Short notification title (e.g., "Timesheet Approved") |
| `message` | `TEXT` | `NOT NULL` | — | Human-readable notification body |
| `metadata` | `JSONB` | `NULL` | `NULL` | Structured extra data: e.g., `{"submission_id": "uuid", "week_start": "2026-05-18", "rejection_note": "..."}` |
| `read_at` | `TIMESTAMPTZ` | `NULL` | `NULL` | `NULL` = unread. Set to `NOW()` when user reads |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |

---

### 4.19 `audit_logs`

Immutable audit trail for all security-sensitive mutations. Required for financial time-tracking applications. Records who did what, to which entity, and when.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | `UUID` | `PRIMARY KEY` | `gen_random_uuid()` | — |
| `workspace_id` | `UUID` | `NULL FK → workspaces(id) ON DELETE SET NULL` | `NULL` | `NULL` for user-level actions (account deletion, login) |
| `actor_user_id` | `UUID` | `NULL FK → users(id) ON DELETE SET NULL` | `NULL` | The user who performed the action. `NULL` for system-triggered actions (timer auto-stop, scheduled cleanup) |
| `action` | `audit_action` | `NOT NULL` | — | What happened |
| `entity_type` | `TEXT` | `NOT NULL` | — | The type of the affected record (e.g., `time_entry`, `timesheet_submission`, `workspace_member`, `project`) |
| `entity_id` | `UUID` | `NULL` | `NULL` | The ID of the affected record. `NULL` for bulk actions |
| `old_values` | `JSONB` | `NULL` | `NULL` | Snapshot of the record's relevant fields before the change. `NULL` for `create` actions |
| `new_values` | `JSONB` | `NULL` | `NULL` | Snapshot of the record's relevant fields after the change. `NULL` for `delete` actions |
| `ip_address` | `INET` | `NULL` | `NULL` | Requester's IP address. Set from the `X-Forwarded-For` header behind the ALB |
| `user_agent` | `TEXT` | `NULL` | `NULL` | Client user agent string |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `NOW()` | — |

**Audit log is append-only.** No `UPDATE` or `DELETE` is ever issued against this table by the application. The service layer writes to it; no trigger manages it (to keep trigger complexity low and give the application full control over what is logged).

**Events that must be logged:**
- Any Admin override of a locked time entry (`lock_override`)
- Role changes for workspace members (`role_change`)
- Timesheet approve/reject actions
- Invite generation and revocation
- Workspace soft-deletion
- User account anonymization

**Indexes:**
```sql
CREATE INDEX ix_audit_logs_workspace_created
ON audit_logs (workspace_id, created_at DESC);

CREATE INDEX ix_audit_logs_actor_created
ON audit_logs (actor_user_id, created_at DESC);

CREATE INDEX ix_audit_logs_entity
ON audit_logs (entity_type, entity_id);
```

---

## 5. Constraints & Business Rules

### Summary of All Partial Unique Indexes

| Index | Table | Condition | Enforces |
|-------|-------|-----------|---------|
| `uq_time_entries_one_running` | `time_entries` | `WHERE status = 'running'` | One running timer per user per workspace |
| `uq_timesheet_submissions_one_pending` | `timesheet_submissions` | `WHERE status = 'pending'` | No double submission of the same week |
| `uq_submission_entries_one_submission_per_entry` | `submission_entries` | (no filter — entire column unique) | Each entry belongs to at most one submission at a time |

### Rate Hierarchy Resolution (Application Logic)

The effective hourly rate for a time entry is resolved by `rate_service.resolve_rate()` in this priority order:

1. `tasks.hourly_rate_cents` (highest priority)
2. `projects.hourly_rate_cents`
3. `clients.hourly_rate_cents`
4. `workspaces.default_hourly_rate_cents` (lowest priority)

If all are `NULL`, `time_entries.hourly_rate_cents` is stored as `NULL` and `billable_amount_cents` is `NULL`. The entry is still logged; it simply has no monetary value.

This resolution happens on every save operation: `stop_timer`, `create_manual_entry`, and `update_entry`. Rate changes after save do not affect existing entries.

### Lock Enforcement Logic (Application Layer)

The database stores all the data needed for lock enforcement; the rules are enforced in `time_entry_service.py`:

| Entry Status | Approval Workflow Off | Approval Workflow On |
|---|---|---|
| `draft` | Editable if not older than `lock_period_days` | Editable if not older than `lock_period_days` |
| `running` | Always editable by owner | Always editable by owner |
| `pending` | N/A (no pending state when workflow off) | Locked to member; cannot edit or delete |
| `approved` | Editable if not older than `lock_period_days` | Locked regardless of date |
| **Admin** | Can always edit any entry | Can always edit any entry |

---

## 6. Indexes

| Index Name | Table | Columns | Type | Purpose |
|------------|-------|---------|------|---------|
| `uq_time_entries_one_running` | `time_entries` | `(user_id, workspace_id)` WHERE `status='running'` | Unique partial | One running timer per user per workspace |
| `ix_time_entries_user_start` | `time_entries` | `(user_id, start_time DESC)` | Composite | User-scoped timesheet and report queries |
| `ix_time_entries_workspace_project` | `time_entries` | `(workspace_id, project_id)` | Composite | Project-level summaries |
| `ix_time_entries_workspace_start` | `time_entries` | `(workspace_id, start_time DESC)` | Composite | Workspace-wide reports |
| `ix_time_entries_workspace_status` | `time_entries` | `(workspace_id, status)` | Composite | Approval queue — pending entries |
| `ix_users_email_lower` | `users` | `LOWER(email)` | Functional | Case-insensitive email lookup |
| `ix_invites_token` | `invites` | `(token)` | Unique | Fast join-link lookup |
| `ix_invites_workspace_expires` | `invites` | `(workspace_id, expires_at)` | Composite | Listing pending invites |
| `ix_workspace_members_user` | `workspace_members` | `(user_id)` | B-tree | Get all workspaces a user belongs to |
| `ix_projects_workspace_status` | `projects` | `(workspace_id, status)` | Composite | Active project listing |
| `ix_tasks_workspace` | `tasks` | `(workspace_id)` | B-tree | Workspace-scoped task queries |
| `ix_tasks_project` | `tasks` | `(project_id)` | B-tree | Project task listing |
| `ix_notifications_user_workspace_read` | `notifications` | `(user_id, workspace_id, read_at)` | Composite | Unread notification count and listing |
| `uq_timesheet_submissions_one_pending` | `timesheet_submissions` | `(workspace_id, user_id, week_start)` WHERE `status='pending'` | Unique partial | Prevent double-submission |
| `ix_timesheet_submissions_workspace_status` | `timesheet_submissions` | `(workspace_id, status)` | Composite | Pending approvals dashboard |
| `uq_submission_entries_one_per_entry` | `submission_entries` | `(time_entry_id)` | Unique | Each entry in at most one submission |
| `ix_audit_logs_workspace_created` | `audit_logs` | `(workspace_id, created_at DESC)` | Composite | Workspace audit trail queries |
| `ix_audit_logs_actor_created` | `audit_logs` | `(actor_user_id, created_at DESC)` | Composite | User action history |
| `ix_audit_logs_entity` | `audit_logs` | `(entity_type, entity_id)` | Composite | Entity-specific audit trail |
| `ix_webhook_delivery_logs_webhook` | `webhook_delivery_logs` | `(webhook_id, attempted_at DESC)` | Composite | Recent delivery history per webhook |
| `ix_password_reset_tokens_user` | `password_reset_tokens` | `(user_id)` | B-tree | Clean up prior tokens on new request |

---

## 7. Triggers

All `updated_at` columns are maintained by a single reusable PostgreSQL trigger function, not by application code. This ensures consistency regardless of how the record is modified (application, admin tools, migration scripts).

```sql
-- Reusable trigger function
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Applied to every table that has an updated_at column:
CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_workspaces_updated_at
  BEFORE UPDATE ON workspaces
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_clients_updated_at
  BEFORE UPDATE ON clients
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tasks_updated_at
  BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_time_entries_updated_at
  BEFORE UPDATE ON time_entries
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_timesheet_submissions_updated_at
  BEFORE UPDATE ON timesheet_submissions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_saved_report_views_updated_at
  BEFORE UPDATE ON saved_report_views
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_webhooks_updated_at
  BEFORE UPDATE ON webhooks
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

**Tables without `updated_at` (append-only or immutable):** `password_reset_tokens`, `workspace_members`, `project_members`, `tags`, `time_entry_tags`, `submission_entries`, `webhook_delivery_logs`, `notifications`, `audit_logs`.

---

## 8. Cascading & Referential Actions

| Parent | Child | On Delete | Rationale |
|--------|-------|-----------|-----------|
| `workspaces` | `workspace_members` | `CASCADE` | Workspace deletion removes all memberships |
| `workspaces` | `invites` | `CASCADE` | — |
| `workspaces` | `clients` | `CASCADE` | — |
| `workspaces` | `projects` | `CASCADE` | — |
| `workspaces` | `tags` | `CASCADE` | — |
| `workspaces` | `time_entries` | `CASCADE` | — |
| `workspaces` | `timesheet_submissions` | `CASCADE` | — |
| `workspaces` | `saved_report_views` | `CASCADE` | — |
| `workspaces` | `webhooks` | `CASCADE` | — |
| `workspaces` | `notifications` | `CASCADE` | — |
| `workspaces` | `audit_logs` | `SET NULL` | Audit records must survive workspace deletion for compliance |
| `projects` | `tasks` | `CASCADE` | Tasks have no meaning outside their project |
| `projects` | `project_members` | `CASCADE` | — |
| `projects` | `time_entries` | `RESTRICT` | Prevent deletion if entries exist; archive the project instead |
| `clients` | `projects` | `SET NULL` | Projects survive client deletion; `client_id` becomes `NULL` |
| `tasks` | `time_entries` | `SET NULL` | Entry history preserved when a task is deleted |
| `users` | `workspace_members` | `RESTRICT` | Anonymize user before removing membership |
| `users` | `time_entries` | `RESTRICT` | Anonymize user; entries remain with anonymized `user_id` |
| `users` | `timesheet_submissions` | `RESTRICT` | Same |
| `users` | `invites (created_by)` | `RESTRICT` | Same |
| `users` | `password_reset_tokens` | `CASCADE` | Tokens are useless after account deletion |
| `users` | `saved_report_views` | `CASCADE` | Views are personal; delete with account |
| `users` | `notifications` | `CASCADE` | — |
| `users` | `audit_logs (actor)` | `SET NULL` | Audit record survives; actor becomes anonymous |
| `webhooks` | `webhook_delivery_logs` | `CASCADE` | — |
| `timesheet_submissions` | `submission_entries` | `CASCADE` | — |
| `time_entries` | `submission_entries` | `CASCADE` | — |
| `time_entries` | `time_entry_tags` | `CASCADE` | — |
| `tags` | `time_entry_tags` | `CASCADE` | Removing a tag removes it from all entries |

---

## 9. Monetary Storage Convention

All monetary values are stored as **`BIGINT` integer cents** (e.g., `$12.50` → `1250`). No `FLOAT`, `DOUBLE`, or `NUMERIC` for monetary columns.

**Columns following this convention:**
- `workspaces.default_hourly_rate_cents`
- `clients.hourly_rate_cents`
- `projects.hourly_rate_cents`, `projects.budget_amount_cents`
- `tasks.hourly_rate_cents`
- `time_entries.hourly_rate_cents`, `time_entries.billable_amount_cents`

**API serialization:** All monetary values are serialized to the API as **strings with two decimal places** (e.g., `"12.50"`) to avoid JSON floating-point precision loss. The API layer divides cents by 100 on the way out and multiplies by 100 on the way in.

**`billable_amount_cents` computation:**
```python
billable_amount_cents = round((duration_seconds / 3600.0) * hourly_rate_cents)
```
This is computed in the service layer and stored. It is not a generated/computed column — storing it allows efficient reporting queries without re-computation.

---

## 10. API Endpoint ↔ Table Mapping

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
| `PATCH/DELETE /time-entries/{id}` | `time_entries`, `time_entry_tags`, `audit_logs` |
| `POST /approvals/submit` | `timesheet_submissions`, `submission_entries`, `time_entries`, `notifications` |
| `GET /approvals/pending` | `timesheet_submissions`, `submission_entries`, `time_entries` |
| `POST /approvals/{id}/approve` | `timesheet_submissions`, `time_entries`, `notifications`, `audit_logs`, `webhook_delivery_logs` |
| `POST /approvals/{id}/reject` | `timesheet_submissions`, `time_entries`, `notifications`, `audit_logs`, `webhook_delivery_logs` |
| `GET /reports/summary` | `time_entries`, `projects`, `clients`, `users` |
| `GET /reports/detailed` | `time_entries`, `projects`, `tasks`, `clients`, `users`, `tags` |
| `GET /reports/*/export` | Same as above → CSV stream |
| `GET /reports/saved-views` | `saved_report_views` |
| `POST /reports/saved-views` | `saved_report_views` |
| `DELETE /reports/saved-views/{id}` | `saved_report_views` |
| `GET/POST/DELETE /webhooks` | `webhooks` |
| `GET /notifications` | `notifications` |
| `POST /notifications/read` | `notifications` |

---

## 11. Migration & Version Control

- **Tool**: Alembic (included in `backend/pyproject.toml`).
- **Location**: `backend/alembic/versions/`.
- **Naming convention**: `YYYYMMDD_HHMM_<descriptive_slug>.py` (e.g., `20260523_0900_initial_schema.py`).
- **Every migration must implement both `upgrade()` and `downgrade()`**. Migrations without a working `downgrade()` are not merged.
- **The initial migration** (`0001_initial_schema`) creates all tables, enums, indexes, triggers, and constraints defined in this document in a single transaction.
- **Subsequent migrations** are one logical change per file (e.g., `0002_add_project_color_column`).
- **CI enforcement**: The GitHub Actions pipeline runs `alembic upgrade head` against the test database on every push to `main`. If migrations fail, the pipeline fails.
- **Data migrations**: If a migration modifies existing data (backfill), the data transformation logic runs inside the `upgrade()` function using SQLAlchemy Core expressions — never raw `psycopg2` calls with user-supplied strings.

---

## 12. Appendix A — Full SQL DDL

The complete DDL is provided here as the definitive reference for the initial Alembic migration. Alembic generates Python code that produces equivalent SQL.

```sql
-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()

-- ============================================================
-- ENUMS
-- ============================================================
CREATE TYPE workspace_role AS ENUM ('admin', 'manager', 'member', 'viewer');
CREATE TYPE project_visibility AS ENUM ('public', 'private');
CREATE TYPE project_status AS ENUM ('active', 'archived');
CREATE TYPE entry_status AS ENUM ('draft', 'running', 'pending', 'approved');
CREATE TYPE submission_status AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE rounding_mode AS ENUM ('none', 'nearest', 'up', 'down');
CREATE TYPE webhook_event_type AS ENUM (
  'time_entry.created',
  'time_entry.updated',
  'timesheet.submitted',
  'timesheet.approved',
  'timesheet.rejected'
);
CREATE TYPE notification_event_type AS ENUM (
  'timesheet_submitted',
  'timesheet_approved',
  'timesheet_rejected',
  'timer_auto_stopped',
  'workspace_deleted'
);
CREATE TYPE audit_action AS ENUM (
  'create', 'update', 'delete',
  'approve', 'reject', 'submit',
  'lock_override', 'role_change',
  'invite_generated', 'invite_revoked',
  'workspace_soft_deleted'
);
CREATE TYPE webhook_delivery_status AS ENUM ('success', 'failed', 'retrying');

-- ============================================================
-- TRIGGER FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE users (
  id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  email             TEXT         NOT NULL UNIQUE,
  password_hash     TEXT,
  google_id         TEXT         UNIQUE,
  full_name         TEXT         NOT NULL,
  avatar_url        TEXT,
  timezone          TEXT,
  weekly_hours_goal SMALLINT     CHECK (weekly_hours_goal > 0),
  is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
  is_superadmin     BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX ix_users_email_lower ON users (LOWER(email));
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE password_reset_tokens (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token       TEXT        NOT NULL UNIQUE,
  expires_at  TIMESTAMPTZ NOT NULL DEFAULT NOW() + interval '1 hour',
  used        BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_prt_expires CHECK (expires_at > created_at)
);
CREATE INDEX ix_password_reset_tokens_user ON password_reset_tokens (user_id);

CREATE TABLE workspaces (
  id                          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
  name                        TEXT           NOT NULL,
  logo_url                    TEXT,
  default_timezone            TEXT           NOT NULL DEFAULT 'UTC',
  date_format                 TEXT           NOT NULL DEFAULT 'MM/DD/YYYY'
                                             CHECK (date_format IN ('MM/DD/YYYY','DD/MM/YYYY')),
  currency                    CHAR(3)        NOT NULL DEFAULT 'USD',
  default_hourly_rate_cents   BIGINT         CHECK (default_hourly_rate_cents >= 0),
  rounding_mode               rounding_mode  NOT NULL DEFAULT 'none',
  rounding_interval_minutes   SMALLINT       CHECK (rounding_interval_minutes IN (1,5,6,10,15,30)),
  mandatory_description       BOOLEAN        NOT NULL DEFAULT FALSE,
  max_timer_duration_seconds  INTEGER        NOT NULL DEFAULT 86400 CHECK (max_timer_duration_seconds > 0),
  past_entry_limit_days       SMALLINT       NOT NULL DEFAULT 7 CHECK (past_entry_limit_days >= 0),
  lock_period_days            SMALLINT       NOT NULL DEFAULT 7 CHECK (lock_period_days >= 0),
  approval_workflow_enabled   BOOLEAN        NOT NULL DEFAULT FALSE,
  idle_detection_enabled      BOOLEAN        NOT NULL DEFAULT FALSE,
  idle_timeout_minutes        SMALLINT       CHECK (idle_timeout_minutes IN (1,2,5,10,15)),
  deleted_at                  TIMESTAMPTZ,
  created_at                  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_ws_rounding CHECK (
    rounding_mode = 'none' OR (rounding_mode != 'none' AND rounding_interval_minutes IS NOT NULL)
  ),
  CONSTRAINT chk_ws_idle CHECK (
    idle_detection_enabled = FALSE OR (idle_detection_enabled = TRUE AND idle_timeout_minutes IS NOT NULL)
  )
);
CREATE TRIGGER trg_workspaces_updated_at BEFORE UPDATE ON workspaces FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE workspace_members (
  workspace_id        UUID            NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id             UUID            NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  role                workspace_role  NOT NULL DEFAULT 'member',
  joined_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
  invited_by_user_id  UUID            REFERENCES users(id) ON DELETE SET NULL,
  PRIMARY KEY (workspace_id, user_id)
);
CREATE INDEX ix_workspace_members_user ON workspace_members (user_id);

CREATE TABLE invites (
  id                 UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id       UUID            NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  email              TEXT            NOT NULL,
  role               workspace_role  NOT NULL DEFAULT 'member'
                                     CHECK (role IN ('manager','member','viewer')),
  token              TEXT            NOT NULL UNIQUE,
  expires_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW() + interval '7 days',
  used               BOOLEAN         NOT NULL DEFAULT FALSE,
  used_by_user_id    UUID            REFERENCES users(id) ON DELETE SET NULL,
  used_at            TIMESTAMPTZ,
  revoked            BOOLEAN         NOT NULL DEFAULT FALSE,
  revoked_at         TIMESTAMPTZ,
  created_by_user_id UUID            NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_inv_expires      CHECK (expires_at > created_at),
  CONSTRAINT chk_inv_used         CHECK ((used = TRUE AND used_at IS NOT NULL) OR (used = FALSE AND used_at IS NULL)),
  CONSTRAINT chk_inv_revoked      CHECK ((revoked = TRUE AND revoked_at IS NOT NULL) OR (revoked = FALSE AND revoked_at IS NULL)),
  CONSTRAINT chk_inv_not_both     CHECK (NOT (used = TRUE AND revoked = TRUE))
);
CREATE UNIQUE INDEX ix_invites_token ON invites (token);
CREATE INDEX ix_invites_workspace_expires ON invites (workspace_id, expires_at);

CREATE TABLE clients (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id        UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name                TEXT        NOT NULL,
  email               TEXT,
  phone               TEXT,
  hourly_rate_cents   BIGINT      CHECK (hourly_rate_cents >= 0),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, name)
);
CREATE TRIGGER trg_clients_updated_at BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE projects (
  id                   UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id         UUID               NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  client_id            UUID               REFERENCES clients(id) ON DELETE SET NULL,
  name                 TEXT               NOT NULL,
  default_billable     BOOLEAN            NOT NULL DEFAULT TRUE,
  budget_hours         NUMERIC(10,2)      CHECK (budget_hours > 0),
  budget_amount_cents  BIGINT             CHECK (budget_amount_cents > 0),
  visibility           project_visibility NOT NULL DEFAULT 'public',
  status               project_status     NOT NULL DEFAULT 'active',
  hourly_rate_cents    BIGINT             CHECK (hourly_rate_cents >= 0),
  color                CHAR(7)            CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
  archived_at          TIMESTAMPTZ,
  created_at           TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, name),
  CONSTRAINT chk_proj_archived CHECK (
    (status = 'archived' AND archived_at IS NOT NULL) OR
    (status = 'active'   AND archived_at IS NULL)
  )
);
CREATE INDEX ix_projects_workspace_status ON projects (workspace_id, status);
CREATE TRIGGER trg_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE project_members (
  project_id          UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  added_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  added_by_user_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
  PRIMARY KEY (project_id, user_id)
);

CREATE TABLE tasks (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id        UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  project_id          UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name                TEXT        NOT NULL,
  assignee_user_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
  estimated_hours     NUMERIC(8,2) CHECK (estimated_hours > 0),
  billable_override   BOOLEAN,
  hourly_rate_cents   BIGINT      CHECK (hourly_rate_cents >= 0),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (project_id, name)
);
CREATE INDEX ix_tasks_workspace ON tasks (workspace_id);
CREATE INDEX ix_tasks_project ON tasks (project_id);
CREATE TRIGGER trg_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE tags (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name         TEXT        NOT NULL,
  color        CHAR(7)     CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE time_entries (
  id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id          UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id               UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  project_id            UUID         NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
  task_id               UUID         REFERENCES tasks(id) ON DELETE SET NULL,
  description           TEXT,
  billable              BOOLEAN      NOT NULL DEFAULT TRUE,
  status                entry_status NOT NULL DEFAULT 'draft',
  start_time            TIMESTAMPTZ  NOT NULL,
  end_time              TIMESTAMPTZ,
  duration_seconds      INTEGER      CHECK (duration_seconds >= 0),
  hourly_rate_cents     BIGINT       CHECK (hourly_rate_cents >= 0),
  billable_amount_cents BIGINT       CHECK (billable_amount_cents >= 0),
  created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_te_end_after_start  CHECK (end_time IS NULL OR end_time > start_time),
  CONSTRAINT chk_te_running_no_end   CHECK (status != 'running' OR (end_time IS NULL AND duration_seconds IS NULL)),
  CONSTRAINT chk_te_done_has_end     CHECK (status = 'running' OR status = 'draft' OR (end_time IS NOT NULL AND duration_seconds IS NOT NULL))
);
CREATE UNIQUE INDEX uq_time_entries_one_running ON time_entries (user_id, workspace_id) WHERE status = 'running';
CREATE INDEX ix_time_entries_user_start ON time_entries (user_id, start_time DESC);
CREATE INDEX ix_time_entries_workspace_project ON time_entries (workspace_id, project_id);
CREATE INDEX ix_time_entries_workspace_start ON time_entries (workspace_id, start_time DESC);
CREATE INDEX ix_time_entries_workspace_status ON time_entries (workspace_id, status);
CREATE TRIGGER trg_time_entries_updated_at BEFORE UPDATE ON time_entries FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE time_entry_tags (
  time_entry_id UUID NOT NULL REFERENCES time_entries(id) ON DELETE CASCADE,
  tag_id        UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (time_entry_id, tag_id)
);

CREATE TABLE timesheet_submissions (
  id                  UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id        UUID              NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id             UUID              NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  week_start          DATE              NOT NULL,
  status              submission_status NOT NULL DEFAULT 'pending',
  submitted_at        TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
  reviewed_by_user_id UUID              REFERENCES users(id) ON DELETE SET NULL,
  reviewed_at         TIMESTAMPTZ,
  rejection_note      TEXT,
  created_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_ts_week_is_monday    CHECK (EXTRACT(DOW FROM week_start) = 1),
  CONSTRAINT chk_ts_rejection_note    CHECK (status != 'rejected' OR (rejection_note IS NOT NULL AND TRIM(rejection_note) != '')),
  CONSTRAINT chk_ts_reviewed_at       CHECK ((status = 'pending' AND reviewed_at IS NULL) OR (status != 'pending' AND reviewed_at IS NOT NULL))
);
CREATE UNIQUE INDEX uq_timesheet_submissions_one_pending
  ON timesheet_submissions (workspace_id, user_id, week_start) WHERE status = 'pending';
CREATE INDEX ix_timesheet_submissions_workspace_status ON timesheet_submissions (workspace_id, status);
CREATE TRIGGER trg_timesheet_submissions_updated_at BEFORE UPDATE ON timesheet_submissions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE submission_entries (
  submission_id  UUID NOT NULL REFERENCES timesheet_submissions(id) ON DELETE CASCADE,
  time_entry_id  UUID NOT NULL REFERENCES time_entries(id) ON DELETE CASCADE,
  PRIMARY KEY (submission_id, time_entry_id)
);
CREATE UNIQUE INDEX uq_submission_entries_one_per_entry ON submission_entries (time_entry_id);

CREATE TABLE saved_report_views (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name         TEXT        NOT NULL,
  report_type  TEXT        NOT NULL CHECK (report_type IN ('summary','detailed')),
  filters      JSONB       NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, user_id, name)
);
CREATE TRIGGER trg_saved_report_views_updated_at BEFORE UPDATE ON saved_report_views FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE webhooks (
  id                UUID                 PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id      UUID                 NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  url               TEXT                 NOT NULL CHECK (url LIKE 'https://%'),
  secret            TEXT,
  subscribed_events webhook_event_type[] NOT NULL,
  is_active         BOOLEAN              NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ          NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_webhooks_updated_at BEFORE UPDATE ON webhooks FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE webhook_delivery_logs (
  id              UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
  webhook_id      UUID                    NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
  workspace_id    UUID                    NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  event_type      webhook_event_type      NOT NULL,
  payload         JSONB                   NOT NULL,
  attempt_number  SMALLINT                NOT NULL DEFAULT 1 CHECK (attempt_number BETWEEN 1 AND 3),
  status          webhook_delivery_status NOT NULL DEFAULT 'retrying',
  http_status_code SMALLINT,
  response_body   TEXT,
  error_message   TEXT,
  attempted_at    TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_webhook_delivery_logs_webhook ON webhook_delivery_logs (webhook_id, attempted_at DESC);

CREATE TABLE notifications (
  id           UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID                    NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id      UUID                    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event_type   notification_event_type NOT NULL,
  title        TEXT                    NOT NULL,
  message      TEXT                    NOT NULL,
  metadata     JSONB,
  read_at      TIMESTAMPTZ,
  created_at   TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_notifications_user_workspace_read ON notifications (user_id, workspace_id, read_at);

CREATE TABLE audit_logs (
  id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id  UUID         REFERENCES workspaces(id) ON DELETE SET NULL,
  actor_user_id UUID         REFERENCES users(id) ON DELETE SET NULL,
  action        audit_action NOT NULL,
  entity_type   TEXT         NOT NULL,
  entity_id     UUID,
  old_values    JSONB,
  new_values    JSONB,
  ip_address    INET,
  user_agent    TEXT,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_audit_logs_workspace_created ON audit_logs (workspace_id, created_at DESC);
CREATE INDEX ix_audit_logs_actor_created ON audit_logs (actor_user_id, created_at DESC);
CREATE INDEX ix_audit_logs_entity ON audit_logs (entity_type, entity_id);
```
