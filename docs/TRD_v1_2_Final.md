# Technical Requirements Document (TRD) – Yusi Time MVP
**Version:** 1.2 (Final — 5 Clockify-Gap Features Added)
**Date:** 2026-05-26
**Status:** Finalized ✅
**Stack:** Next.js 14 (App Router) · TypeScript strict · Tailwind CSS 3 (darkMode: class) · shadcn/ui · next-themes · FastAPI (Python 3.12+) · PostgreSQL 15 · AWS
**Aligned With:** PRD v1.3 (Final)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-22 | Initial draft |
| 1.1 | 2026-05-23 | PRD reference updated to v1.2; monorepo structure added; JWT storage strategy resolved; webhook retry aligned; invite link endpoints added; approval toggle transition added to services; rate snapshot coverage completed; pagination threshold defined; local email dev strategy added; `app/` directory placeholder documented |
| 1.2 | 2026-05-26 | **PRD reference updated to v1.3. 5 Clockify-gap features integrated:** `continue_entry()` and `duplicate_entry()` added to `time_entry_service.py`; `get_weekly_report()` added to `report_service.py`; `useDescriptionDraft` hook added to frontend; `/reports/weekly` route added; rate_service coverage extended to continue/duplicate; testing section updated with new test cases; frontend routing updated; Headless UI replaced by shadcn/ui; dual light/dark theme system (next-themes) documented; design tokens updated to CSS variable system; new frontend dependencies added |
| 1.3 | 2026-05-31 | **Super Admin backend added (API-only pass).** `is_superadmin` boolean column added to `User` model. `get_workspace_member()` dependency updated with synthetic member bypass. `require_role()` updated with unconditional Super Admin bypass. New `get_superadmin_user()` dependency added. `UserPublic` schema updated. No frontend changes. No new routers in this pass. Full architecture documented in DB Schema v2.2 Changelog §12. |

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Technology Stack](#2-technology-stack)
3. [Monorepo Structure](#3-monorepo-structure)
4. [Architecture Overview](#4-architecture-overview)
5. [Development Environment & Setup](#5-development-environment--setup)
6. [Backend Implementation Details](#6-backend-implementation-details)
   - [6.1 Project Structure](#61-project-structure)
   - [6.2 Configuration & Core](#62-configuration--core)
   - [6.3 Database & ORM](#63-database--orm)
   - [6.4 API Design & Endpoints](#64-api-design--endpoints)
   - [6.5 Authentication & Authorization](#65-authentication--authorization)
   - [6.6 Business Logic Services](#66-business-logic-services)
   - [6.7 Webhooks](#67-webhooks)
   - [6.8 Error Handling & Logging](#68-error-handling--logging)
   - [6.9 Testing](#69-testing)
7. [Frontend (Web) Implementation Details](#7-frontend-web-implementation-details)
   - [7.1 Project Structure](#71-project-structure)
   - [7.2 Routing & Pages](#72-routing--pages)
   - [7.3 State Management](#73-state-management)
   - [7.4 API Client & Data Fetching](#74-api-client--data-fetching)
   - [7.5 Token Storage Strategy](#75-token-storage-strategy)
   - [7.6 Validation](#76-validation)
   - [7.7 Idle Detection Implementation](#77-idle-detection-implementation)
   - [7.8 Description Draft Auto-Save](#78-description-draft-auto-save)
   - [7.9 Animations & Transitions](#79-animations--transitions)
   - [7.10 Styling, Design Tokens & Theming](#710-styling-design-tokens--theming)
8. [Mobile App (Flutter) – Post-MVP Blueprint](#8-mobile-app-flutter--post-mvp-blueprint)
9. [Security Measures](#9-security-measures)
10. [Deployment on AWS](#10-deployment-on-aws)
11. [Appendices](#11-appendices)
    - [A. Environment Variables](#a-environment-variables)
    - [B. Key Dependencies & Versions](#b-key-dependencies--versions)
    - [C. Mermaid Architecture Diagram](#c-mermaid-architecture-diagram)

---

## 1. Introduction

This document defines the complete technical implementation for the Yusi Time MVP.
It serves as the single source of technical truth alongside **PRD v1.3 (Final)**
and the Database Schema & API Specification. All design decisions, architectural
patterns, and integration details are described here.

**Document Authority Rule**: If a conflict exists between documents, PRD v1.3
takes precedence for *what* to build; this TRD takes precedence for *how* to
build it. The Database Schema & API Specification is the authoritative source
for all table definitions, field types, and endpoint contracts.

---

## 2. Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Web Frontend** | Next.js 14+ (App Router), React 18+, TypeScript (strict) | App Router with server and client components as appropriate |
| **UI Components** | shadcn/ui | Built on Radix UI primitives. Replaces Headless UI. All interactive components use shadcn exclusively |
| **Theming** | next-themes | Light/dark/system theme toggle. `darkMode: 'class'` in Tailwind. CSS variables drive the full color system |
| **State Management** | TanStack Query (React Query v5) for server state; Zustand for UI-only state | No Redux. All hooks-based |
| **Styling** | Tailwind CSS 3+ (`darkMode: 'class'`) | Semantic CSS variable tokens in `globals.css`. Never raw hex in components |
| **Animations** | Framer Motion | Micro-interactions and page transitions only. Duration 0.2–0.3s. `MotionConfig reducedMotion="user"` in root layout |
| **Form Handling** | React Hook Form + Zod | Schema-based client-side validation. Zod schemas mirror server Pydantic models |
| **Icons** | lucide-react exclusively | No other icon library permitted |
| **Toast** | sonner | Replaces shadcn Toast for all notifications including the mandatory rounding toast |
| **Mobile App (post-MVP)** | Flutter 3.x (Dart), Riverpod, Dio, freezed | Reuses the same REST API. Not in MVP scope |
| **Backend Framework** | FastAPI (Python 3.12+) | Async throughout; auto-generated OpenAPI 3.1 docs |
| **ORM / DB Toolkit** | SQLAlchemy 2.0 (async mode) + Alembic | Declarative models, async sessions, migration scripts |
| **Validation** | Pydantic V2 | All request/response schemas |
| **Authentication** | Custom JWT (access + refresh) + OAuth2 (Google) | Argon2 for password hashing |
| **Database** | PostgreSQL 15 | Hosted on AWS RDS |
| **Email** | AWS SES (password reset only) | Only transactional email in MVP. Local dev uses console/log fallback |
| **Deployment** | AWS Amplify (web), ECS Fargate (API), RDS, CloudFront | CI/CD via GitHub Actions |
| **Monitoring** | CloudWatch Logs; structured JSON logging via structlog | No third-party APM in MVP |

---

## 3. Monorepo Structure

```
yusi-time/                        # Git repository root
├── backend/                      # FastAPI Python application
├── web/                          # Next.js web application
├── app/                          # Flutter mobile app — POST-MVP ONLY
│                                 # ⚠️ Do NOT scaffold or modify during MVP phases.
│                                 # This directory is a placeholder reserved for
│                                 # the future Flutter application.
├── .github/
│   └── workflows/
│       ├── backend.yml           # Backend CI/CD pipeline
│       └── web.yml               # Web CI/CD pipeline
├── docker-compose.yml            # Local dev: PostgreSQL + backend + web
├── .gitignore
└── README.md
```

**Critical rule for AI agents**: Never create, modify, or delete any file inside
`app/` during MVP development. All MVP work is confined to `backend/` and `web/`.

---

## 4. Architecture Overview

Three-tier architecture:
- **Presentation**: Next.js (AWS Amplify / CloudFront) + future Flutter (post-MVP)
- **Application**: FastAPI REST API — stateless, containerized, ECS Fargate behind ALB
- **Data**: PostgreSQL on Amazon RDS, encrypted at rest, automated backups

Both clients communicate exclusively over HTTPS with the API. All input validated
server-side using Pydantic. API interacts with DB exclusively through SQLAlchemy
async sessions — never raw SQL with user-supplied strings.

---

## 5. Development Environment & Setup

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20 LTS | Web frontend |
| pnpm | Latest stable | Web package manager |
| Python | 3.12 | Backend |
| Poetry | Latest stable | Backend dependency management |
| Docker & Docker Compose | Latest stable | Local PostgreSQL |
| AWS CLI | v2 | Deployment |

### Local Startup

```bash
# From monorepo root — start PostgreSQL
docker-compose up -d db

# Backend
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000

# Web (separate terminal)
cd web
pnpm install
pnpm dev
```

### Local Email (Password Reset)
- `APP_ENV=development` → reset link logged to stdout (no SES required locally)
- `APP_ENV=staging|production` → AWS SES used normally

---

## 6. Backend Implementation Details

### 6.1 Project Structure

```
backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── user.py
│   │   ├── workspace.py
│   │   ├── workspace_member.py
│   │   ├── invite.py
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── project_member.py
│   │   ├── task.py
│   │   ├── time_entry.py
│   │   ├── tag.py
│   │   ├── webhook.py
│   │   └── notification.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── workspace.py
│   │   ├── invite.py
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── time_entry.py
│   │   ├── approval.py
│   │   ├── report.py
│   │   ├── webhook.py
│   │   └── notification.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── workspaces.py
│   │   ├── invites.py
│   │   ├── clients.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── time_entries.py
│   │   ├── approvals.py
│   │   ├── reports.py
│   │   ├── webhooks.py
│   │   └── notifications.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── invite_service.py
│   │   ├── time_entry_service.py   # continue_entry, duplicate_entry added
│   │   ├── approval_service.py
│   │   ├── rate_service.py
│   │   ├── rounding_service.py
│   │   ├── report_service.py       # get_weekly_report added
│   │   ├── notification_service.py
│   │   └── webhook_service.py
│   ├── utils/
│   │   ├── email.py
│   │   └── pagination.py
│   └── main.py
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
├── pyproject.toml
└── .env.example
```

### 6.2 Configuration & Core

**`config.py`** — `pydantic-settings` `BaseSettings`. Fails fast on startup if
any required variable is missing.

```python
class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    jwt_secret: str
    jwt_refresh_secret: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    invite_link_expire_hours: int = 168      # 7 days per PRD v1.3
    google_client_id: str
    google_client_secret: str
    aws_ses_region: str = "us-east-1"
    aws_access_key_id: str
    aws_secret_access_key: str
    frontend_url: str
```

**`security.py`** — JWT create/verify, Argon2 hashing, `secrets.token_urlsafe(32)`.

**`dependencies.py`** — FastAPI dependency functions:
- `get_db()` → yields `AsyncSession`; commits on success, rolls back on exception
- `get_current_user(token)` → decodes access token, fetches user. Raises `401` if invalid
- `get_workspace_member(workspace_id, current_user)` → verifies membership. Raises `403` if not member
- `require_role(*roles)` → factory that raises `403` if role insufficient

### 6.3 Database & ORM

- All primary keys: UUID v4 (`gen_random_uuid()`)
- All timestamps: `TIMESTAMPTZ`, stored in UTC
- Multi-tenancy: `workspace_id` FK on every workspace-scoped table, included in every query
- SQLAlchemy `relationship()` with explicit `back_populates`
- All migrations via Alembic. Every change requires a reversible migration script

**No schema changes are required for the 5 new features:**
- Continue entry: creates a new `time_entries` row — existing schema sufficient
- Duplicate entry: creates a new `time_entries` row — existing schema sufficient
- Description draft: `localStorage` only — no DB change
- Weekly report: queries existing `time_entries` joined to `users` — no new tables
- Dashboard continue: reuses existing `POST /time-entries/start` — no change

### 6.4 API Design & Endpoints

**Base path**: `/api/v1/`
**Auth**: `Authorization: Bearer <access_token>` on all endpoints except public ones.
**Docs**: Swagger UI at `/docs`; ReDoc at `/redoc`. Both disabled in production.

**Request/Response format:**
- JSON payloads
- ISO 8601 timestamps with timezone offset
- Durations: integer seconds
- Monetary amounts: strings with 2 decimal places (`"125.50"`)

**Pagination:**
- Cursor-based for endpoints that can exceed 200 rows: `GET /time-entries`, `GET /reports/detailed`
- Limit-offset for all other list endpoints

**Full endpoint list**: See API Spec v1.1. Total: 76 endpoints.

**New endpoints in v1.2 (corresponding to API Spec v1.1):**
- `POST /time-entries/{id}/continue` — continue entry as new timer
- `POST /time-entries/{id}/duplicate` — duplicate entry to today
- `GET /reports/weekly` — weekly per-user per-day report
- `GET /reports/weekly/export` — CSV export of weekly report

### 6.5 Authentication & Authorization

**Email/password signup:**
1. Validate unique email (case-insensitive). Raise `409` if duplicate.
2. Hash password with Argon2.
3. Create `User` record.
4. Create default workspace `[User Name]'s Workspace` with user as Admin.
5. Return access token + set refresh token as HttpOnly cookie.

**Token storage:**
- Access token: signed HS256 JWT, 30 minutes, returned in JSON body
- Refresh token: signed HS256 JWT, 7 days, HttpOnly Secure SameSite=Strict cookie

**JWT payload:**
```json
{ "sub": "<user_uuid>", "type": "access", "iat": 1716000000, "exp": 1716001800 }
```

`workspace_id` is NOT in the JWT — passed per-request as path/query param.

**Authorization flow per request:**
1. `get_current_user` → decode access token
2. `get_workspace_member` → confirm workspace membership (or bypass for Super Admin)
3. `require_role` → confirm role meets endpoint requirement (or bypass for Super Admin)
All via FastAPI `Depends()` chaining.

**Super Admin authorization bypass:**

Super Admin (`is_superadmin = TRUE`) short-circuits the standard authorization
flow at steps 2 and 3. The implementation lives entirely in `dependencies.py`
and requires zero changes to any router or service.

- **Step 2 bypass (`get_workspace_member`):** Returns a synthetic `WorkspaceMember`
  object constructed in memory with `role='admin'`. The `workspace_members` table
  is never queried. All downstream response serialization treats the Super Admin
  as a workspace admin, ensuring full financial data visibility and no Viewer
  data isolation restrictions.

- **Step 3 bypass (`require_role`):** The inner `_require_role` function injects
  `current_user` via `Depends(get_current_user)` in addition to `member`. When
  `current_user.is_superadmin is True`, the function returns `member` immediately
  without evaluating `member.role` against the required roles list.

- **Super Admin-only endpoints (`get_superadmin_user`):** A dedicated dependency
  that raises `403 FORBIDDEN` for any user where `is_superadmin is False`. Used
  on platform-operator endpoints (to be added in the post-Phase 2 UI pass).
  Current MVP has no endpoints using this dependency — it is added now to
  establish the pattern cleanly.

**What Super Admin does NOT change:**
- JWT structure and validation — unchanged
- Token expiry — unchanged
- Google OAuth flow — unchanged
- Password reset flow — unchanged
- The `UserPublic` schema now includes `is_superadmin: bool` so the frontend
  can read the flag from `GET /users/me` and gate future UI elements

### 6.6 Business Logic Services

All business rules live exclusively in the service layer.
Routers: validate input, call one service function, return result. No business logic in routers.

---

#### `auth_service.py`
- `register(email, password, name)` → creates user + default workspace; returns tokens. `is_superadmin` is always set to `FALSE` on new user creation regardless of input. The field is not present in `SignupRequest` schema.
- `login(email, password)` → verifies credentials; returns tokens
- `refresh_tokens(refresh_token)` → verifies refresh token; returns new access token
- `initiate_password_reset(email)` → generates secure token, stores with 1h expiry, calls `email.py`
- `reset_password(token, new_password)` → validates token, updates password, invalidates token

---

#### `invite_service.py`
- `create_invite(admin_user, workspace_id, invitee_email, role)` → generates `secrets.token_urlsafe(32)` token; stores `Invite` with `expires_at = now() + 7 days`; returns full invite URL
- `list_pending_invites(workspace_id)` → returns invites where `used=False AND revoked=False AND expires_at > now()`
- `revoke_invite(admin_user, workspace_id, token)` → sets `revoked=True`. Raises `403` if not Admin
- `validate_invite(token)` → raises `400` if expired/revoked/used; returns workspace name and role
- `accept_invite(current_user, token)` → calls `validate_invite`; adds user to workspace; marks `used=True`; raises `409` if already member

---

#### `time_entry_service.py`

- `start_timer(user, workspace_id, project_id, task_id, description, tags, billable, force)`:
  1. Check for running timer for this user in this workspace
  2. If found and `force=False`: raise `409 TIMER_ALREADY_RUNNING`
  3. If found and `force=True`: call `stop_timer` on existing entry
  4. Validate project visibility and membership
  5. Create entry with `status=running`, `start_time=now()`
  6. Snapshot rate via `rate_service.resolve_rate()` and store on entry
  7. Return new entry

- `stop_timer(user, entry_id, idle_end_time=None)`:
  1. Fetch entry; verify it belongs to user and `status=running`
  2. Compute raw duration: `(idle_end_time or now()) - start_time` in seconds
  3. Apply rounding: `rounding_service.round_duration(raw_seconds, workspace_rounding_rule)`
  4. Persist `duration_seconds` (rounded), `end_time`, `status=draft`
  5. Return `{entry, raw_seconds, rounded_seconds, rounding_rule}`

- `create_manual_entry(user, workspace_id, data)`:
  1. Validate `start_time < end_time`
  2. Validate `start_time >= (today - workspace.past_entry_limit_days)`. Raise `400` if exceeded
  3. Check for overlapping entries; flag `has_overlap=True` if found (soft warning)
  4. Apply rounding to raw duration
  5. Snapshot rate via `rate_service.resolve_rate()`
  6. Return `{entry, raw_seconds, rounded_seconds, has_overlap}`

- `update_entry(user, entry_id, data)`:
  1. Fetch entry; check lock status:
     - `status == pending` or `status == approved`: raise `403 ENTRY_LOCKED` (non-Admins)
     - Older than `lock_period_days` and not Admin: raise `403 ENTRY_LOCKED`
  2. Apply rounding to new raw duration (re-rounds from newly submitted value per PRD v1.3 §3.3.7)
  3. Re-snapshot rate via `rate_service.resolve_rate()`
  4. Persist changes
  5. Return `{entry, raw_seconds, rounded_seconds}`

- `delete_entry(user, entry_id)`:
  1. Fetch entry; apply same lock checks as `update_entry`
  2. Hard-delete the record

- **`continue_entry(user, workspace_id, entry_id, force)` (NEW — v1.2)**:
  1. Fetch source entry; verify it belongs to the workspace
  2. Verify caller has access:
     - Member: can only continue own entries. Raise `403 FORBIDDEN` if entry belongs to another user
     - Manager/Admin: can continue any entry in workspace
  3. Verify `source_entry.status != 'pending'`. Raise `400 CANNOT_CONTINUE_PENDING` if pending
  4. If another timer is running and `force=False`: raise `409 TIMER_ALREADY_RUNNING`
  5. If another timer is running and `force=True`: call `stop_timer` on running entry first
  6. Create new entry with:
     - `project_id` = source `project_id`
     - `task_id` = source `task_id`
     - `description` = source `description`
     - `billable` = source `billable`
     - Tags copied from source entry (insert rows in `time_entry_tags`)
     - `status` = `running`
     - `start_time` = `NOW()`
     - Fresh rate snapshot via `rate_service.resolve_rate()`
  7. Return `{new_entry, source_entry_id}`
  - **Note**: The source entry is never modified. A completely new entry record is created.

- **`duplicate_entry(user, workspace_id, entry_id)` (NEW — v1.2)**:
  1. Fetch source entry; verify it belongs to the workspace
  2. Verify caller has access:
     - Member: own entries only. Raise `403 FORBIDDEN` for other user's entries
     - Manager/Admin: any entry in workspace
  3. Verify `source_entry.status != 'pending'`. Raise `400 CANNOT_DUPLICATE_PENDING` if pending
  4. Compute new entry's start_time:
     - `start_time` = start of current calendar day in workspace timezone (midnight local, converted to UTC)
     - `end_time` = `start_time` + `source_entry.duration_seconds`
  5. Compute raw duration = `source_entry.duration_seconds`
  6. Apply rounding: `rounding_service.round_duration(raw_duration, workspace_rounding_rule)`
  7. Fresh rate snapshot via `rate_service.resolve_rate()`
  8. Compute `billable_amount_cents`
  9. Create new draft entry with all source metadata (project, task, description, billable, tags)
  10. Return `{new_entry, rounding, source_entry_id}`
  - **Note**: Source entry is never modified. Rounding toast response always included.

---

#### `approval_service.py`

- `submit_week(user, workspace_id, week_start)`:
  1. Derive `week_end = week_start + 6 days`
  2. Fetch entries for `user` within week where `status == 'draft'`. Approved entries explicitly excluded per PRD v1.3 §3.6.2
  3. If no qualifying entries: raise `400 NO_ENTRIES_TO_SUBMIT`
  4. Set all qualifying entries to `status=pending`
  5. Create `TimesheetSubmission` record linking user, workspace, week_start, submitted entry IDs
  6. Fire `timesheet.submitted` webhook event
  7. Create in-app notifications for all Managers and Admins

- `approve_submission(manager, submission_id)`:
  1. Verify caller is Manager or Admin
  2. Fetch submission; verify `status == 'pending'`
  3. Set all linked entries to `status=approved`
  4. Update submission: `status=approved`, record `reviewed_by` and `reviewed_at`
  5. Fire `timesheet.approved` webhook
  6. Create in-app notification for submitting member

- `reject_submission(manager, submission_id, note)`:
  1. Verify caller is Manager or Admin
  2. Validate `note` is non-empty. Raise `422` if blank
  3. Set all linked entries back to `status=draft`
  4. Update submission: `status=rejected`, store rejection note
  5. Fire `timesheet.rejected` webhook
  6. Create in-app notification for submitting member, including rejection note

- `toggle_approval_workflow(admin, workspace_id, enabled)`:
  1. Verify caller is Admin
  2. Update `workspace.approval_workflow_enabled`
  3. If `enabled=False`:
     - Pending entries: remain `status=pending` (locked). Admin must manually review
     - Approved entries: fall under rolling lock date going forward
     - Draft entries: fall under rolling lock date immediately
  4. If `enabled=True`: no changes to existing entries. Applies to new submissions going forward

---

#### `rate_service.py`

- `resolve_rate(workspace_id, project_id, task_id, user_id)`:
  1. Task-level rate (highest priority)
  2. Project-level rate
  3. Client-level rate
  4. Workspace default rate (lowest priority)
  5. Returns `None` if no rate defined at any level
- Called on **every** time entry save: `stop_timer`, `create_manual_entry`,
  `update_entry`, **`continue_entry`** (NEW), **`duplicate_entry`** (NEW)
- Continue and Duplicate both take a **fresh rate snapshot** — they never inherit
  the source entry's stored rate

---

#### `rounding_service.py`

- `round_duration(duration_seconds, rule)`:
  - `rule`: `mode` (none|nearest|up|down) + `interval_minutes` (1,5,6,10,15,30)
  - `none`: return unchanged
  - `nearest`: round to nearest interval
  - `up`: ceiling to next interval
  - `down`: floor to previous interval
  - Always returns integer seconds
- Called on every save including **`duplicate_entry`** (NEW)

---

#### `report_service.py`

- `get_summary(workspace_id, caller_role, group_by, date_from, date_to, filters)` → grouped summary
- `get_detailed(workspace_id, caller_role, filters, cursor, limit)` → cursor-paginated entry list
- **`get_weekly_report(workspace_id, caller_role, date_from, date_to, user_id, project_id, billable)` (NEW — v1.2)**:
  1. Authorization check:
     - If `caller_role` is `member` or `viewer`: lock `user_id` to `current_user.id`.
       If a different `user_id` was supplied, raise `403 FORBIDDEN`
     - If `caller_role` is `manager` or `admin`: no user restriction
  2. Build list of all calendar days between `date_from` and `date_to` (max 31 days)
  3. Query `time_entries` joined to `users` for the workspace and date range,
     grouped by `(user_id, DATE(start_time))`, aggregating:
     - `SUM(duration_seconds)` → total seconds for that user+day
     - `SUM(CASE WHEN billable THEN duration_seconds ELSE 0)` → billable seconds
     - `SUM(CASE WHEN billable THEN billable_amount_cents ELSE 0)` → billable amount
     - `COUNT(id)` → entry count
  4. Build response structure: one row per user with a dict of day totals
  5. Apply Viewer data isolation: omit `billable_hours`, `total_billable_amount`,
     `grand_total_billable_amount` from response for `viewer` role
  6. Return structured weekly grid response per API Spec v1.1 §14
- `export_summary(...)` → CSV stream
- `export_detailed(...)` → CSV stream
- **`export_weekly(...)` (NEW — v1.2)** → CSV stream, one row per user per day

---

#### `webhook_service.py`
- `dispatch(workspace_id, event, payload)`:
  1. Load all webhook URLs subscribed to `event`
  2. Enqueue delivery using `FastAPI BackgroundTasks`
  3. Deliver via `httpx.AsyncClient` with 10s timeout
  4. Retry: 3 attempts, exponential backoff (5s → 25s → 125s)
  5. After 3 failures: log at ERROR level, stop

---

#### `notification_service.py`
- `create(workspace_id, user_id, event_type, message, metadata)` → inserts Notification
- `create_for_role(workspace_id, role, event_type, message, metadata)` → creates for all members of role
- `mark_read(user_id, notification_ids)` → sets `read_at = now()`
- `mark_all_read(user_id, workspace_id)` → bulk update

---

### 6.7 Webhooks

Events: `time_entry.created`, `time_entry.updated`, `timesheet.submitted`,
`timesheet.approved`, `timesheet.rejected`.

Payload structure:
```json
{
  "event": "timesheet.approved",
  "timestamp": "2026-05-22T09:00:00+00:00",
  "workspace_id": "<uuid>",
  "data": { }
}
```

Retry: 3 attempts (5s → 25s → 125s). Failures logged at ERROR after exhaustion.
HMAC-SHA256 signing via `X-Yusitime-Signature` header if secret set.

### 6.8 Error Handling & Logging

```json
{ "detail": "Human-readable error message", "code": "MACHINE_READABLE_CODE" }
```

| Code | Usage |
|------|-------|
| 400 | Business rule violation, bad input, CANNOT_CONTINUE_PENDING, CANNOT_DUPLICATE_PENDING |
| 401 | Unauthenticated |
| 403 | Forbidden / lock violation |
| 404 | Not found |
| 409 | Conflict (duplicate email, TIMER_ALREADY_RUNNING, etc.) |
| 422 | Pydantic validation failure |
| 500 | Unhandled server error |

Logging via `structlog` JSON format. Every log: `request_id`, `user_id`,
`workspace_id`, `endpoint`, `method`, `status_code`, `duration_ms`.

### 6.9 Testing

**Unit tests** (`tests/unit/`):
Every service function has tests with mocked DB sessions.

Critical cases (original + new):
- Rounding edge cases (0 seconds, exactly on interval boundary)
- Invite expiry logic and single-use enforcement
- Rate hierarchy resolution (all four levels)
- Lock enforcement (member cannot edit pending/approved/date-locked)
- Approval toggle transition
- Viewer response schema (financial fields absent)
- Timer singleton (409 when timer running without force)
- **`continue_entry` — pending source entry returns `400 CANNOT_CONTINUE_PENDING`** (NEW)
- **`continue_entry` — Member cannot continue another member's entry (403)** (NEW)
- **`continue_entry` — force=True stops running timer before starting new** (NEW)
- **`continue_entry` — fresh rate snapshot taken (not inherited from source)** (NEW)
- **`duplicate_entry` — pending source entry returns `400 CANNOT_DUPLICATE_PENDING`** (NEW)
- **`duplicate_entry` — start_time set to today midnight in workspace timezone** (NEW)
- **`duplicate_entry` — rounding applied to duplicated duration** (NEW)
- **`duplicate_entry` — billable_amount_cents computed and stored** (NEW)
- **`get_weekly_report` — Member sees only own row** (NEW)
- **`get_weekly_report` — Viewer financial fields absent** (NEW)
- **`get_weekly_report` — zero-hour days included with entry_count=0** (NEW)
- **`get_workspace_member` — Super Admin returns synthetic member with role='admin' without DB query** (NEW v1.3)
- **`require_role` — Super Admin bypasses all role checks unconditionally** (NEW v1.3)
- **`get_superadmin_user` — non-super-admin user returns 403 FORBIDDEN** (NEW v1.3)
- **`register` — newly created user always has `is_superadmin=False`** (NEW v1.3)
- **Super Admin accesses workspace endpoint without membership — 200 success** (NEW v1.3)

**Integration tests** (`tests/integration/`):
Real test DB, full HTTP flows via `httpx.AsyncClient`.

Key flows (original + new):
1. Signup → create project → start timer → stop timer → verify rounding
2. Admin generates invite → user accepts → user is workspace member with correct role
3. Member submits week → Manager approves → entries locked as approved
4. Member submits week → Manager rejects with note → entries unlock → member resubmits
5. Admin disables approval workflow → pending entries stay locked
6. Viewer calls report endpoint → financial fields absent from response
7. **Member continues a draft entry → new timer starts with same metadata** (NEW)
8. **Member continues a pending entry → 400 CANNOT_CONTINUE_PENDING** (NEW)
9. **Member duplicates draft entry → new draft created with today's date, rounding toast included** (NEW)
10. **Admin/Manager requests weekly report → all member rows returned** (NEW)
11. **Member requests weekly report → only own row returned** (NEW)
12. **Weekly report export → valid CSV with correct columns, no financial data for Viewer** (NEW)

**Coverage target**: ≥ 80% for service layer. Checked in CI via `pytest-cov`.

---

## 7. Frontend (Web) Implementation Details

### 7.1 Project Structure

```
web/
├── public/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout: ThemeProvider, QueryClientProvider,
│   │   │                           # Toaster (sonner), MotionConfig
│   │   ├── page.tsx                # Redirect: auth→/dashboard, anon→/login
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── signup/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   └── reset-password/page.tsx
│   │   ├── join/[token]/page.tsx   # Invite acceptance (public)
│   │   └── (app)/
│   │       ├── layout.tsx          # AppShell: Sidebar, TimerBar, IdleModal
│   │       ├── dashboard/page.tsx
│   │       ├── timesheet/page.tsx
│   │       ├── projects/
│   │       │   ├── page.tsx
│   │       │   └── [id]/page.tsx
│   │       ├── reports/
│   │       │   ├── summary/page.tsx
│   │       │   ├── detailed/page.tsx
│   │       │   └── weekly/page.tsx   # NEW — v1.2
│   │       ├── approvals/page.tsx
│   │       └── settings/
│   │           ├── workspace/page.tsx
│   │           ├── members/page.tsx
│   │           ├── clients/page.tsx
│   │           ├── tags/page.tsx
│   │           ├── webhooks/page.tsx
│   │           └── profile/page.tsx
│   ├── components/
│   │   ├── ui/                     # shadcn primitives only
│   │   └── shared/                 # StatusBadge, EmptyState, PageHeader,
│   │                               # ConfirmDialog, RoleBadge, TableRowSkeleton
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── schemas.ts
│   │   ├── timer/
│   │   │   ├── components/         # TimerBar, IdleModal
│   │   │   ├── hooks/              # useCurrentTimer, useStartTimer, useStopTimer,
│   │   │   │                       # useContinueEntry, useDescriptionDraft
│   │   │   └── idle-detector.ts
│   │   ├── time-entries/
│   │   │   ├── components/         # TimeEntryRow, AddEntrySheet, EditEntrySheet
│   │   │   ├── hooks/              # useTimeEntries, useContinueEntry,
│   │   │   │                       # useDuplicateEntry
│   │   │   ├── api.ts
│   │   │   └── schemas.ts
│   │   ├── projects/
│   │   ├── timesheet/
│   │   │   ├── components/         # WeeklyGrid, GridCell, SubmitWeekModal
│   │   │   └── hooks/
│   │   ├── approvals/
│   │   ├── reports/
│   │   │   ├── components/         # FilterBar, SummaryTable, WeeklyReportGrid
│   │   │   └── hooks/              # useSummaryReport, useDetailedReport,
│   │   │                           # useWeeklyReport
│   │   ├── settings/
│   │   └── notifications/
│   ├── hooks/
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── query-client.ts
│   │   └── utils.ts                # cn(), formatDuration(), formatMoney(),
│   │                               # descriptionDraftKey()
│   ├── stores/
│   │   ├── timer-store.ts          # isIdle, idleStartTime, setIdle, clearIdle
│   │   ├── workspace-store.ts      # activeWorkspaceId, setWorkspaceId
│   │   └── ui-store.ts             # sidebarOpen, activeModal
│   ├── styles/
│   │   └── globals.css             # CSS variable system (light + dark tokens)
│   └── middleware.ts
├── tailwind.config.ts              # darkMode: 'class', semantic color tokens
├── next.config.js
├── tsconfig.json                   # strict: true
└── package.json
```

### 7.2 Routing & Pages

**Public routes:**
- `/` → redirect to `/dashboard` (auth) or `/login` (anon)
- `/login`, `/signup`, `/forgot-password`, `/reset-password`
- `/join/[token]` → invite acceptance page

**Protected routes** (auth guard in `(app)/layout.tsx` and `middleware.ts`):
- `/dashboard`
- `/timesheet`
- `/projects`, `/projects/[id]`
- `/reports/summary`, `/reports/detailed`
- `/reports/weekly` **(NEW — v1.2)** — accessible to all roles; Members/Viewers see own row only
- `/approvals` — Manager/Admin only; redirect others to `/dashboard`
- `/settings/workspace`, `/settings/members`, `/settings/clients`,
  `/settings/tags`, `/settings/webhooks`, `/settings/profile`

**Middleware behavior:** On access to protected route without valid token in
memory, attempt silent refresh via `POST /auth/refresh`. On failure: redirect to
`/login?redirect=<current-path>`.

### 7.3 State Management

**Server state (TanStack Query):**
- All API data fetched and cached by React Query
- Feature module hooks with typed query key factories:
  - `useProjects(workspaceId)`, `useProject(id)`, `useTasks(projectId)`
  - `useTimeEntries(filters)`, `useCurrentTimer()` (polled every 5s)
  - `usePendingApprovals(workspaceId)`, `useReportSummary(params)`
  - `useWeeklyReport(params)` **(NEW — v1.2)**
  - `useNotifications()`, `useWorkspaceMembers(workspaceId)`
- Mutations invalidate related query keys on success
- `useContinueEntry()` **(NEW)** — invalidates `['timer']`, `['time-entries']`, `['dashboard']`
- `useDuplicateEntry()` **(NEW)** — invalidates `['time-entries']`, `['dashboard']`; shows rounding toast on success

**Stale time guide:**
```
timer (current):  0ms + refetchInterval: 5000
time entries:     30_000ms
projects/tasks:   60_000ms
reports:          120_000ms
members/settings: 300_000ms
weekly report:    120_000ms
```

**UI state (Zustand):**
- `timer-store.ts`:
  - `isRunning`, `startTime`, `currentEntryId`, `isIdle`, `idleStartTime`
  - Actions: `setRunning`, `setIdle`, `clearIdle`, `clearTimer`
  - Optimistically updated on start/stop; reconciled against server every 5s
- `workspace-store.ts`:
  - `activeWorkspaceId`
  - `setWorkspaceId(id)` → invalidates all queries via `queryClient.clear()`
- `ui-store.ts`:
  - `sidebarOpen`, `activeModal`
  - Actions: `toggleSidebar`, `openModal`, `closeModal`

### 7.4 API Client & Data Fetching

`lib/api-client.ts` exports a configured Axios instance:

```typescript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,  // required for HttpOnly refresh cookie
})

// Request interceptor: attach access token from memory
apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: silent refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      try {
        const { data } = await apiClient.post('/auth/refresh')
        tokenStore.setAccessToken(data.access_token)
        error.config.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(error.config)
      } catch {
        tokenStore.clearAccessToken()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

All feature-level API calls in typed service functions in `features/[feature]/api.ts`.
These functions are used inside React Query hooks — never called directly from components.

**New API functions (v1.2):**
```typescript
// features/time-entries/api.ts
export const timeEntriesApi = {
  // ... existing functions ...
  continue: (entryId: string, params: { workspaceId: string; force?: boolean }) =>
    apiClient.post(`/time-entries/${entryId}/continue`, { force: params.force ?? false },
      { params: { workspace_id: params.workspaceId } }),
  duplicate: (entryId: string, params: { workspaceId: string }) =>
    apiClient.post(`/time-entries/${entryId}/duplicate`, {},
      { params: { workspace_id: params.workspaceId } }),
}

// features/reports/api.ts
export const reportsApi = {
  // ... existing functions ...
  weekly: (params: WeeklyReportParams) =>
    apiClient.get('/reports/weekly', { params }),
  weeklyExport: (params: WeeklyReportParams) =>
    apiClient.get('/reports/weekly/export', { params, responseType: 'blob' }),
}
```

### 7.5 Token Storage Strategy

| Token | Storage | Rationale |
|-------|---------|-----------|
| **Access token** (30 min) | JS memory (`tokenStore` module variable) | Never on disk. Lost on refresh; recovered via refresh token. Not XSS-accessible |
| **Refresh token** (7 days) | HttpOnly Secure SameSite=Strict cookie | Not JS-accessible. Auto-sent on refresh. SameSite=Strict prevents CSRF |

**On page load:** Call `POST /auth/refresh` silently. Success: restore token.
Failure: redirect to `/login`.

### 7.6 Validation

- Zod schemas in `features/[feature]/schemas.ts` mirror Pydantic server schemas exactly
- React Hook Form + `@hookform/resolvers/zod`
- Server 422 errors mapped back to form fields via `form.setError()`
- **Rounding preview:** Manual entry form computes rounded duration client-side
  (pure function, no API call) and displays preview before save
- **Continue/Duplicate:** No form needed — actions are immediate. Confirmation prompt
  only when a timer is already running (standard timer-conflict dialog)

### 7.7 Idle Detection Implementation

Custom hook `useIdleDetector(timeoutMs, enabled)`:

Events monitored: `mousemove`, `mousedown`, `keydown`, `touchstart`, `scroll`, `visibilitychange`

**State machine:**
1. **Active**: timer running; activity resets countdown
2. **Idle**: timeout expires while `isRunning=true` → `setIdle(true, idleStartTime)`; display shows "Idle: X min"
3. **Prompted**: first interaction after idle → `openModal('idle')`; all background interaction blocked

**Three modal options:**
- **Keep Time & Continue**: `clearIdle()` — timer continues. No API call.
- **Discard Idle & Stop**: `POST /time-entries/{id}/stop` with `idle_end_time` = idleStartTime → `showRoundingToast`
- **Discard Idle & Continue**: `POST /time-entries/{id}/stop` with `idle_end_time` = idleStartTime,
  then `POST /time-entries/start` with same `project_id`, `task_id`, `description` → `showRoundingToast`

**Modal constraints:** shadcn `Dialog` with `onPointerDownOutside={e => e.preventDefault()}`,
`onEscapeKeyDown={e => e.preventDefault()}`, and `[&>button]:hidden` to remove X button.
User MUST choose one of three options.

**Cross-device:** Strictly per-device, per-browser-tab. Server has no idle state concept.

### 7.8 Description Draft Auto-Save (NEW — v1.2)

**Hook:** `useDescriptionDraft(userId, workspaceId)`
**Location:** `features/timer/hooks/useDescriptionDraft.ts`

```typescript
const DRAFT_KEY = (userId: string, wsId: string) =>
  `yt_desc_draft_${userId}_${wsId}`

export function useDescriptionDraft(userId: string, workspaceId: string) {
  const key = DRAFT_KEY(userId, workspaceId)

  const getDraft = (): string =>
    typeof window !== 'undefined' ? localStorage.getItem(key) ?? '' : ''

  const saveDraft = (value: string): void => {
    if (typeof window === 'undefined') return
    if (value) localStorage.setItem(key, value)
    else localStorage.removeItem(key)
  }

  const clearDraft = (): void => {
    if (typeof window !== 'undefined') localStorage.removeItem(key)
  }

  return { getDraft, saveDraft, clearDraft }
}
```

**Integration in TimerBar:**
- On component mount: if no timer is running, call `getDraft()` and populate description field
- If a timer IS running on mount: use server description from `useCurrentTimer()` data; call `clearDraft()`
- On every `onChange` of the description input: call `saveDraft(value)` (debounced 500ms)
- On successful `startTimer()` or `stopTimer()`: call `clearDraft()`
- On user explicitly clearing the description field: call `clearDraft()`

**Constraints:**
- `localStorage` only — never sent to server
- Scoped per `userId` + `workspaceId` to prevent cross-user or cross-workspace leakage
- Graceful no-op in SSR context (`typeof window === 'undefined'` guard)

### 7.9 Animations & Transitions

Framer Motion — all durations **0.2–0.3s**. `MotionConfig reducedMotion="user"` in root layout.

| Element | Animation |
|---------|-----------|
| Page transitions | `opacity` fade 0→1, 0.18s |
| Timer running | Opacity pulse 1→0.4→1, 2s loop (applied to the running indicator dot via animate-timer-pulse) |
| List items | `AnimatePresence` + y-slide 4px + `opacity`, stagger 0.04s (max 5 items) |
| Modals | `scale` 0.97→1 + `opacity`, 0.20s |
| Toast (sonner) | Slide up y:12→0 + `opacity`, 0.22s |
| Continue button press | `active:scale-[0.97]`, 80ms |

**Rules:**
- Only animate `opacity` and `transform` — never `width`, `height`, `padding`
- Every animation must convey meaning — if you can't explain why it exists, remove it
- Never two competing animations simultaneously on the same screen

### 7.10 Styling, Design Tokens & Theming

**Theme system:** `next-themes` + Tailwind `darkMode: 'class'` + CSS variables.
Three components required:
- `ThemeProvider` wrapper in `app/layout.tsx`
- `ThemeToggle` component (Sun/Moon DropdownMenu) in Sidebar footer
- Full CSS variable system in `globals.css`

**Color system:** Semantic CSS variables only. Never raw hex in component code.

```css
/* globals.css — abbreviated */
:root {
  --background: 0 0% 99%;         /* page bg */
  --surface: 0 0% 100%;           /* card bg */
  --surface-raised: 0 0% 97%;     /* hover surface */
  --primary: 24 100% 50%;         /* #FE6900 */
  --success: 142 71% 45%;         /* #22C55E */
  --warning: 38 92% 50%;          /* #F59E0B */
  --destructive: 0 84% 60%;       /* #EF4444 */
  --status-pending: 258 90% 66%;  /* #8B5CF6 */
  --foreground: 240 10% 4%;
  --border: 220 13% 91%;
  /* ... full system in FRONTEND_SKILL.md §1.3 */
}
.dark {
  --background: 240 5% 6%;        /* #0F0F10 */
  --surface: 240 4% 9%;           /* #16161A */
  --primary: 24 100% 55%;         /* #FE6B00 brighter in dark */
  /* ... full dark system in FRONTEND_SKILL.md §1.3 */
}
```

**Typography:**
- `font-sans` → DM Sans (all UI text)
- `font-mono` → DM Mono (ALL time values, ALL monetary amounts)

**Tailwind config:** `darkMode: ['class']`. All CSS variables mapped to Tailwind
color tokens (see FRONTEND_SKILL.md §1.4).

**Component rules:**
- shadcn for ALL interactive components (Dialog, Select, DropdownMenu, Sheet,
  Tabs, Switch, Table, Command, Avatar, Progress, Popover, Tooltip, AlertDialog, Sonner)
- All imports: `import { Button } from '@/components/ui/button'` (no barrel imports)
- `cn()` for all conditional class merging
- Named exports for all non-page components

**Responsiveness:**
- Minimum: 375px screen width
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Sidebar: always visible lg+, icon-only md, sheet overlay sm
- TimerBar: full md+, compressed sm (project name + timer + stop only)
- Every component tested at sm, md, lg before marking complete

---

## 8. Mobile App (Flutter) – Post-MVP Blueprint

> ⚠️ **For planning reference only. No Flutter code during MVP phases.**

The Flutter app will live in `yusi-time/app/` and consume the same REST API.
- State: Riverpod (`StateNotifier`, `AsyncNotifier`)
- HTTP: Dio with JWT interceptors
- Token storage: `flutter_secure_storage` (refresh); memory (access)
- Models: `freezed` + `json_serializable`
- Idle detection: `AppLifecycleState` via `WidgetsBindingObserver`
- All layouts responsive via `LayoutBuilder`, `MediaQuery`, flexible widgets. Min: 320dp.

---

## 9. Security Measures

**Transport:** TLS 1.3 at CloudFront and ALB. All HTTP redirected to HTTPS.

**XSS:** React JSX automatic escaping. `Content-Security-Policy` in `next.config.js`.
Server-side sanitization via `bleach` on all free-text inputs.

**SQL Injection:** SQLAlchemy ORM + parameterized queries exclusively.

**CSRF:** Access token in-memory (not cookie) → CSRF doesn't apply to most endpoints.
Refresh cookie: `SameSite=Strict` → prevents cross-site CSRF on `/auth/refresh`.

**Rate Limiting:** `slowapi` on `/auth/login`, `/auth/signup`, `/auth/forgot-password`,
`/auth/refresh`. Limit: 10 req/min per IP.

**localStorage Security (NEW — v1.2):**
- `localStorage` used exclusively for description drafts
- Draft keys are scoped to `userId + workspaceId` — never cross-contaminated
- Drafts contain only description text — no tokens, no sensitive financial data
- Users are aware localStorage is cleared on browser data wipe (acceptable per PRD §8)

**Secret Management:** All secrets in AWS Systems Manager Parameter Store / Secrets Manager.
Injected at ECS task runtime. Never hard-coded. `.env.example` has only placeholders.

**Viewer Data Isolation:** Enforced at service + Pydantic schema layer on server.
Different response schemas for Viewer role omit financial fields entirely.
Frontend adds a second layer but server is the authoritative control.

---

## 10. Deployment on AWS

### Web Frontend
- Next.js → AWS Amplify (CI/CD from `main` branch automatically)
- CloudFront CDN for asset caching and TLS termination

### Backend API
- FastAPI in Docker → Amazon ECR → ECS Fargate behind ALB
- MVP: 2 desired tasks for basic HA. Auto-scaling defined but not activated.

### Database
- Amazon RDS PostgreSQL 15. Encrypted at rest (KMS). 7-day automated backups.
- Separate RDS instance for test/CI.

### Email
- AWS SES. Sandbox → verify domains before launch. Dev: console-log fallback.

### CI/CD (GitHub Actions) — on push to `main`:
1. Backend: `ruff` lint + `pytest`. Fail fast on any failure.
2. Frontend: `eslint` lint + `tsc --noEmit`. Fail fast on error.
3. Build Docker image → push to ECR with Git SHA tag
4. Update ECS service (rolling deployment)
5. Build Next.js → deploy to Amplify
6. Secrets injected from GitHub Secrets → AWS Parameter Store → ECS task env

### Monitoring
- CloudWatch Logs (structured JSON from backend)
- Alarms: ECS CPU > 80%, memory > 80%, RDS connections, 5xx rate > 1%
- Frontend: global React `ErrorBoundary`. Amplify monitoring in production.

---

## 11. Appendices

### A. Environment Variables

**Backend (`backend/.env` / ECS):**
```
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/yusitime
JWT_SECRET=<random-256-bit-secret>
JWT_REFRESH_SECRET=<different-random-256-bit-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
INVITE_LINK_EXPIRE_HOURS=168
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
AWS_ACCESS_KEY_ID=<aws-key>
AWS_SECRET_ACCESS_KEY=<aws-secret>
AWS_SES_REGION=us-east-1
FRONTEND_URL=http://localhost:3000
```

**Web (`web/.env.local`):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<same-as-backend>
```

### B. Key Dependencies & Versions

**Backend (Python / Poetry):**
```
fastapi == 0.115.0
uvicorn == 0.30.0
sqlalchemy == 2.0.30
asyncpg == 0.29.0
alembic == 1.13.0
pydantic == 2.8.0
pydantic-settings == 2.3.0
python-jose == 3.3.0
argon2-cffi == 23.1.0
httpx == 0.27.0
slowapi == 0.1.9
bleach == 6.1.0
structlog == 24.4.0
boto3 == 1.34.0
pytest == 8.2.0
pytest-asyncio == 0.23.0
pytest-mock == 3.14.0
ruff == 0.4.0
```

**Web (Node / pnpm):**
```
next == 14.2.0
react == 18.3.0
react-dom == 18.3.0
typescript == 5.4.0
@tanstack/react-query == 5.40.0
zustand == 4.5.0
react-hook-form == 7.51.0
zod == 3.23.0
@hookform/resolvers == 3.4.0
axios == 1.7.0
framer-motion == 11.0.0
next-themes == 0.3.0
tailwindcss == 3.4.0
tailwindcss-animate == 1.0.7
sonner == 1.5.0
class-variance-authority == 0.7.0
clsx == 2.1.0
tailwind-merge == 2.3.0
lucide-react == 0.383.0
@radix-ui/react-dialog == 1.0.5
@radix-ui/react-select == 2.0.0
@radix-ui/react-tabs == 1.0.4
@radix-ui/react-switch == 1.0.3
@radix-ui/react-avatar == 1.0.4
@radix-ui/react-progress == 1.0.3
@radix-ui/react-popover == 1.0.7
@radix-ui/react-dropdown-menu == 2.0.6
@radix-ui/react-tooltip == 1.0.7
@radix-ui/react-alert-dialog == 1.0.5
cmdk == 1.0.0
dm-sans (google font via next/font)
eslint == 8.57.0
```

**Removed (v1.2):**
```
@radix-ui/react-toast — replaced by sonner
```

### C. Mermaid Architecture Diagram

```mermaid
graph TD
    A[User Browser: Next.js App] -->|HTTPS| B[CloudFront CDN]
    B --> C[AWS Amplify: Static Assets]
    B --> D[Application Load Balancer]
    D --> E[ECS Fargate: FastAPI App]
    E --> F[(Amazon RDS: PostgreSQL 15)]
    E --> G[Amazon SES: Password Reset Email]
    E --> H[AWS Parameter Store: Secrets]
    I[GitHub Actions CI/CD] -->|Deploy web| C
    I -->|Push Docker image| J[Amazon ECR]
    J -->|Pull image| E
    K[Mobile App - Post-MVP Flutter] -->|HTTPS| B
```
