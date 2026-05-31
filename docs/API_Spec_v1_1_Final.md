# API Specification – Yusi Time MVP
**Version:** 1.1 (Final — 5 Clockify-Gap Features Added)
**Date:** 2026-05-26
**Status:** Finalized ✅
**Base URL:** `https://api.yusitime.com/api/v1`
**Aligned With:** PRD v1.3 (Final) · TRD v1.1 (Final) · DB Schema v2.0 (Final)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-23 | YusiTime Architect | Initial final specification — all 40 endpoints fully described |
| 1.1 | 2026-05-26 | YusiTime Architect | 3 new endpoints added: `POST /time-entries/{id}/continue`, `POST /time-entries/{id}/duplicate`, `GET /reports/weekly`. Appendix B updated. Error codes updated. Description draft is frontend-only — no API change needed. Dashboard continue reuses existing `POST /time-entries/start`. |
| 1.2 | 2026-05-31 | YusiTime Architect | Super Admin backend added (API-only pass). No new endpoints in this pass. `UserPublic` schema updated to include `is_superadmin: bool`. Role hierarchy table updated. §1.10 updated with Super Admin bypass notes. Post-Phase 2 planned endpoints documented in DB Schema v2.2 Changelog §12. |

---

## Table of Contents

1. [Global Conventions](#1-global-conventions)
2. [Shared Schema Objects](#2-shared-schema-objects)
3. [Auth Endpoints](#3-auth-endpoints)
4. [User Endpoints](#4-user-endpoints)
5. [Workspace Endpoints](#5-workspace-endpoints)
6. [Member Endpoints](#6-member-endpoints)
7. [Invite Endpoints](#7-invite-endpoints)
8. [Client Endpoints](#8-client-endpoints)
9. [Project Endpoints](#9-project-endpoints)
10. [Task Endpoints](#10-task-endpoints)
11. [Tag Endpoints](#11-tag-endpoints)
12. [Time Entry Endpoints](#12-time-entry-endpoints)
13. [Approval Endpoints](#13-approval-endpoints)
14. [Report Endpoints](#14-report-endpoints)
15. [Webhook Endpoints](#15-webhook-endpoints)
16. [Notification Endpoints](#16-notification-endpoints)
17. [Appendix A — Enum Values Reference](#17-appendix-a--enum-values-reference)
18. [Appendix B — Endpoint Summary Table](#18-appendix-b--endpoint-summary-table)

---

## 1. Global Conventions

### 1.1 Base URL & Versioning

```
Production:   https://api.yusitime.com/api/v1
Development:  http://localhost:8000/api/v1
```

All endpoints are prefixed with `/api/v1`. Breaking changes will increment
the version to `/api/v2` (post-MVP).

Interactive documentation:
- Swagger UI: `GET /docs` (disabled in production)
- ReDoc: `GET /redoc` (disabled in production)

---

### 1.2 Authentication

All endpoints require a valid access token **except**:
- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/google`
- `GET /auth/google/callback`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `GET /invites/{token}` (public invite validation)

**Access token delivery:**
```
Authorization: Bearer <access_token>
```

- Access token: signed HS256 JWT, valid for **30 minutes**.
- Refresh token: HttpOnly, Secure, SameSite=Strict cookie named `refresh_token`,
  valid for **7 days**.
- On `401`, clients silently retry via `POST /auth/refresh`. If that also fails,
  redirect to `/login`.

**JWT payload:**
```json
{
  "sub": "<user_uuid>",
  "type": "access",
  "iat": 1716000000,
  "exp": 1716001800
}
```

---

### 1.3 Request Format

- All request bodies: `Content-Type: application/json`.
- Path parameters: lowercase kebab-case UUIDs.
- Query parameters: `snake_case`.
- Boolean query parameters: `true` / `false` (case-insensitive).

---

### 1.4 Response Format

**Single resource:**
```json
{ "data": { } }
```

**List (limit-offset):**
```json
{ "data": [ ], "total": 42, "page": 1, "per_page": 20 }
```

**List (cursor-based):**
```json
{ "data": [ ], "next_cursor": "<string|null>", "limit": 50 }
```

**Empty success:**
```json
{ "message": "Human-readable confirmation" }
```

---

### 1.5 Pagination

**Cursor-based** — endpoints where result set can exceed 200 rows:
- `GET /time-entries`, `GET /reports/detailed`
- Query params: `cursor` (opaque string), `limit` (default 50, max 200)

**Limit-offset** — all other list endpoints:
- Query params: `page` (default 1), `per_page` (default 20, max 100)

---

### 1.6 Monetary Values

All monetary amounts transmitted as **decimal strings** with exactly 2 decimal
places (e.g., `"125.50"`). `null` when no rate defined.

---

### 1.7 Timestamps

- ISO 8601 UTC: `"2026-05-22T09:00:00+00:00"`
- Date-only: `"YYYY-MM-DD"`
- Duration: integer seconds

---

### 1.8 Error Response Format

```json
{
  "detail": "Human-readable description.",
  "code": "MACHINE_READABLE_CODE"
}
```

Validation errors (422):
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email", "code": "VALIDATION_ERROR" }
  ]
}
```

---

### 1.9 Standard Error Codes

| HTTP | `code` | Meaning |
|------|--------|---------|
| `400` | `BAD_REQUEST` | Business rule violation or malformed input |
| `400` | `INVITE_EXPIRED` | Invite link past 7-day expiry |
| `400` | `INVITE_USED` | Invite already accepted |
| `400` | `INVITE_REVOKED` | Admin revoked this invite |
| `400` | `NO_ENTRIES_TO_SUBMIT` | No unlocked/draft entries for the week |
| `400` | `PAST_ENTRY_LIMIT_EXCEEDED` | Entry backdated beyond workspace limit |
| `400` | `INVALID_WEEK_START` | week_start is not a Monday |
| `400` | `CANNOT_CONTINUE_PENDING` | Continue called on a pending entry |
| `400` | `CANNOT_DUPLICATE_PENDING` | Duplicate called on a pending entry |
| `401` | `UNAUTHENTICATED` | Missing or invalid access token |
| `401` | `TOKEN_EXPIRED` | Access token expired |
| `401` | `INVALID_CREDENTIALS` | Email/password mismatch |
| `403` | `FORBIDDEN` | Insufficient role |
| `403` | `ENTRY_LOCKED` | Entry is locked (pending/approved/past lock date) |
| `403` | `SOLE_ADMIN` | Cannot delete — sole Admin of workspace |
| `404` | `NOT_FOUND` | Resource not found |
| `409` | `EMAIL_ALREADY_EXISTS` | Signup with existing email |
| `409` | `TIMER_ALREADY_RUNNING` | Start timer when one is already active |
| `409` | `ALREADY_MEMBER` | User already a workspace member |
| `409` | `DUPLICATE_NAME` | Name already exists in workspace |
| `409` | `ALREADY_SUBMITTED` | Pending submission already exists for this week |
| `422` | `VALIDATION_ERROR` | Pydantic schema validation failure |
| `500` | `INTERNAL_ERROR` | Unhandled server error |

---

### 1.10 Role Hierarchy & Authorization

### 1.10 Role Hierarchy & Authorization

**Super Admin note:** Any user with `is_superadmin = true` on the `users` table
bypasses this entire table unconditionally. They are not a role within the
`workspace_role` enum. They access all workspace endpoints via a synthetic
`admin`-level membership and pass all `require_role` checks regardless of the
required role. See DB Schema v2.2 Changelog §12 for full architecture.
Super Admin-only endpoints (post-Phase 2) will use the `get_superadmin_user`
dependency instead of `require_role`.

| Capability | Admin | Manager | Member | Viewer |
|-----------|-------|---------|--------|--------|
| Manage workspace settings | ✅ | ❌ | ❌ | ❌ |
| Invite members | ✅ | ❌ | ❌ | ❌ |
| Create/edit clients, projects, tasks | ✅ | ✅ | ❌ | ❌ |
| Log time | ✅ | ✅ | ✅ | ❌ |
| Continue entry (own) | ✅ | ✅ | ✅ | ❌ |
| Continue any member's entry | ✅ | ✅ | ❌ | ❌ |
| Duplicate entry (own) | ✅ | ✅ | ✅ | ❌ |
| Duplicate any member's entry | ✅ | ✅ | ❌ | ❌ |
| Edit own unlocked entries | ✅ | ✅ | ✅ | ❌ |
| Edit any member's entries | ✅ | ✅ | ❌ | ❌ |
| Override locked entries | ✅ | ❌ | ❌ | ❌ |
| Submit timesheet | ✅ | ✅ | ✅ | ❌ |
| Approve/reject timesheets | ✅ | ✅ | ❌ | ❌ |
| View all financial data | ✅ | ✅ | ❌ | ❌ |
| View Weekly Report (all members) | ✅ | ✅ | ❌ | ❌ |
| View Weekly Report (own row only) | — | — | ✅ | ✅ |
| Register/manage webhooks | ✅ | ❌ | ❌ | ❌ |

---

### 1.11 Viewer Data Isolation

When the authenticated user's role is `viewer`, the following fields are
**completely absent** from all response payloads (not `null` — absent):

- `hourly_rate` / `hourly_rate_cents`
- `billable_amount` / `billable_amount_cents`
- `default_hourly_rate` / `default_hourly_rate_cents`
- `budget_amount` / `budget_amount_cents`
- `total_billable_amount`
- `currency`

Enforced at the **service and Pydantic schema layer** on the server.

---

## 2. Shared Schema Objects

### `UserPublic`
```json
{
  "id": "uuid",
  "full_name": "string",
  "email": "string",
  "avatar_url": "string | null",
  "timezone": "string | null",
  "weekly_hours_goal": "integer | null",
  "is_superadmin": "boolean",
  "created_at": "datetime"
}
```

### `WorkspaceSummary`
```json
{
  "id": "uuid",
  "name": "string",
  "logo_url": "string | null",
  "role": "admin | manager | member | viewer",
  "created_at": "datetime"
}
```

### `ProjectSummary`
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "string",
  "color": "string | null",
  "status": "active | archived",
  "visibility": "public | private",
  "client_id": "uuid | null",
  "client_name": "string | null"
}
```

### `TaskSummary`
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "name": "string",
  "billable_override": "boolean | null"
}
```

### `TagObject`
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "string",
  "color": "string | null"
}
```

### `TimeEntryObject`
Full time entry. Financial fields omitted for Viewer role.
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "user_name": "string",
  "project_id": "uuid",
  "project_name": "string",
  "project_color": "string | null",
  "task_id": "uuid | null",
  "task_name": "string | null",
  "description": "string | null",
  "billable": "boolean",
  "status": "draft | running | pending | approved",
  "start_time": "datetime",
  "end_time": "datetime | null",
  "duration_seconds": "integer | null",
  "tags": "[TagObject]",
  "hourly_rate": "string | null",
  "billable_amount": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `RoundingResult`
Returned alongside any time entry save operation.
```json
{
  "raw_seconds": "integer",
  "rounded_seconds": "integer",
  "rounding_mode": "none | nearest | up | down",
  "rounding_interval_minutes": "integer | null"
}
```

---

## 3. Auth Endpoints

### `POST /auth/signup`
Register new user with email/password. Creates default workspace.
**Auth required:** No

**Request:**
```json
{ "email": "alex@example.com", "password": "mypassword123", "full_name": "Alex Johnson" }
```

**Success `201`:** Returns `{ user, default_workspace, access_token }`. Sets refresh cookie.

**Errors:** `409 EMAIL_ALREADY_EXISTS`, `422 VALIDATION_ERROR`

---

### `POST /auth/login`
Email/password login. Rate limit: 10 req/min per IP.
**Auth required:** No

**Request:** `{ "email": "...", "password": "..." }`
**Success `200`:** Returns `{ user: UserPublic, access_token }`. Sets refresh cookie.
**Errors:** `401 INVALID_CREDENTIALS`

---

### `POST /auth/refresh`
Exchange HttpOnly refresh cookie for new access token.
**Auth required:** No (cookie-based)
**Success `200`:** `{ "data": { "access_token": "eyJ..." } }`
**Errors:** `401 TOKEN_EXPIRED`, `401 UNAUTHENTICATED`

---

### `POST /auth/logout`
Clear refresh token cookie.
**Auth required:** Yes
**Success `200`:** `{ "message": "Logged out successfully." }`

---

### `GET /auth/google`
Initiate Google OAuth2. Returns `302 Redirect`.
**Auth required:** No

---

### `GET /auth/google/callback`
Handle Google OAuth2 callback. Returns `302 Redirect` to frontend with token.
**Auth required:** No

---

### `POST /auth/forgot-password`
Trigger password reset email. Always returns 200 (prevents enumeration).
Rate limit: 10 req/min per IP.
**Auth required:** No
**Request:** `{ "email": "alex@example.com" }`
**Success `200`:** `{ "message": "If an account with that email exists, a reset link has been sent." }`

---

### `POST /auth/reset-password`
Consume reset token and set new password.
**Auth required:** No
**Request:** `{ "token": "abc123...", "new_password": "mynewpassword456" }`
**Success `200`:** `{ "message": "Password reset successfully." }`
**Errors:** `400 BAD_REQUEST` (token not found / used / expired)

---

## 4. User Endpoints

### `GET /users/me`
Return authenticated user's profile.
**Success `200`:** Returns full user object.

---

### `PATCH /users/me`
Update profile. All fields optional.

| Field | Type | Validation |
|-------|------|-----------|
| `full_name` | `string` | 1–100 chars |
| `avatar_url` | `string \| null` | Valid URL or null |
| `timezone` | `string \| null` | IANA timezone or null |
| `weekly_hours_goal` | `integer \| null` | 1–168 or null |

**Success `200`:** Returns updated user.

---

### `DELETE /users/me`
Anonymize account. Blocked if sole Admin of any workspace.
**Success `200`:** `{ "message": "Account deleted successfully." }`
**Errors:** `403 SOLE_ADMIN`

---

## 5. Workspace Endpoints

### `GET /workspaces`
List all workspaces the user belongs to.
**Success `200`:** List of workspace summaries with user's role.

---

### `POST /workspaces`
Create a new workspace. Creator is added as Admin.
**Request:** `{ "name": "New Agency", "logo_url": null }`
**Success `201`:** Returns full workspace object.

---

### `GET /workspaces/{workspace_id}`
Get workspace details and all settings.
**Auth:** Any workspace member.
**Success `200`:** Full workspace settings object.
**Note:** `default_hourly_rate` omitted for Viewer.

---

### `PATCH /workspaces/{workspace_id}`
Update workspace settings. **Admin only.**

All fields optional. Key validations:
- `rounding_interval_minutes` required when `rounding_mode != "none"`
- `idle_timeout_minutes` required when `idle_detection_enabled = true`
- Setting `approval_workflow_enabled = false` triggers approval toggle transition.

**Success `200`:** Returns updated workspace.
**Errors:** `403 FORBIDDEN`, `422 VALIDATION_ERROR`

---

### `DELETE /workspaces/{workspace_id}`
Soft-delete workspace. **Admin only.** Notifies all members.
**Success `200`:** `{ "message": "Workspace scheduled for deletion in 30 days." }`

---

## 6. Member Endpoints

### `GET /workspaces/{workspace_id}/members`
List all workspace members with roles.
**Auth:** Any member.
**Query:** `page`, `per_page`

---

### `PATCH /workspaces/{workspace_id}/members/{user_id}`
Change a member's role. **Admin only.**
**Request:** `{ "role": "manager | member | viewer" }`
**Business rule:** Cannot set `admin` role via this endpoint. Cannot demote sole Admin.
**Success `200`:** Returns updated membership.
**Errors:** `400 BAD_REQUEST`, `403 FORBIDDEN`, `404 NOT_FOUND`

---

### `DELETE /workspaces/{workspace_id}/members/{user_id}`
Remove a member. **Admin only.** Blocked if removing sole Admin.
**Success `200`:** `{ "message": "Member removed." }`

---

## 7. Invite Endpoints

### `POST /workspaces/{workspace_id}/invites`
Generate invite link. **Admin only.**

**Request:**
```json
{ "email": "newmember@example.com", "role": "member" }
```

**Success `201`:**
```json
{
  "data": {
    "id": "uuid",
    "email": "newmember@example.com",
    "role": "member",
    "invite_url": "https://yusitime.com/join/abc123xyz",
    "token": "abc123xyz",
    "expires_at": "2026-05-29T09:00:00+00:00",
    "created_at": "2026-05-22T09:00:00+00:00"
  }
}
```

**Errors:** `400 BAD_REQUEST` (role=admin), `403 FORBIDDEN`

---

### `GET /workspaces/{workspace_id}/invites`
List pending invites. **Admin only.**
**Query:** `page`, `per_page`

---

### `DELETE /workspaces/{workspace_id}/invites/{token}`
Revoke a pending invite. **Admin only.**
**Success `200`:** `{ "message": "Invite link revoked." }`
**Errors:** `400 INVITE_USED`, `404 NOT_FOUND`

---

### `GET /invites/{token}`
Validate invite token. **No auth required.**
**Success `200`:** `{ "workspace_id", "workspace_name", "role", "expires_at" }`
**Errors:** `400 INVITE_EXPIRED`, `400 INVITE_USED`, `400 INVITE_REVOKED`, `404 NOT_FOUND`

---

### `POST /invites/{token}/accept`
Authenticated user joins workspace.
**Auth required:** Yes

**Behavior:**
1. Validate token (400 if expired/used/revoked)
2. Check not already member (409 if so)
3. Create `workspace_members` record with pre-assigned role
4. Mark invite `used=TRUE`

**Success `200`:** `{ "workspace_id", "workspace_name", "role", "joined_at" }`
**Errors:** `400 INVITE_*`, `409 ALREADY_MEMBER`

---

## 8. Client Endpoints

### `GET /clients`
List clients in workspace. **Any member.**
**Query:** `workspace_id` (required), `page`, `per_page`
**Note:** `hourly_rate` omitted for Viewer.

---

### `POST /clients`
Create client. **Manager/Admin only.**
**Request:** `{ "name", "email?", "phone?", "hourly_rate?" }`
**Success `201`:** Returns client object.
**Errors:** `409 DUPLICATE_NAME`

---

### `GET /clients/{client_id}`
Get single client. **Any member.**

---

### `PATCH /clients/{client_id}`
Update client. **Manager/Admin only.** All fields optional.
**Errors:** `409 DUPLICATE_NAME`

---

### `DELETE /clients/{client_id}`
Delete client. **Admin only.** Sets `client_id = NULL` on linked projects.
**Success `200`:** `{ "message": "Client deleted. Linked projects unassigned." }`

---

## 9. Project Endpoints

### `GET /projects`
List visible projects. Visibility respects role.
**Query:** `workspace_id` (required), `status` (active|archived|all), `client_id`, `page`, `per_page`
**Note:** `budget_amount`, `hourly_rate` omitted for Viewer.

---

### `POST /projects`
Create project. **Manager/Admin only.**

| Field | Required | Validation |
|-------|----------|-----------|
| `name` | ✅ | 1–150 chars, unique in workspace |
| `client_id` | ❌ | Must belong to workspace |
| `default_billable` | ❌ | Default `true` |
| `visibility` | ❌ | `public \| private`, default `public` |
| `hourly_rate` | ❌ | Decimal ≥ `"0.00"` |
| `budget_hours` | ❌ | > 0 |
| `budget_amount` | ❌ | Decimal > `"0.00"` |
| `color` | ❌ | `#RRGGBB` hex |

**Success `201`:** Returns full project.
**Errors:** `403 FORBIDDEN`, `409 DUPLICATE_NAME`

---

### `GET /projects/{project_id}`
Get project. Must have visibility access.

---

### `PATCH /projects/{project_id}`
Update project. **Manager/Admin only.** All fields optional.

---

### `POST /projects/{project_id}/archive`
Archive project. **Manager/Admin only.**
**Success `200`:** `{ "id", "status": "archived", "archived_at" }`

---

### `DELETE /projects/{project_id}`
Hard-delete project. **Admin only.** Blocked if entries exist.
**Errors:** `400 BAD_REQUEST` (entries exist — archive instead)

---

### `GET /projects/{project_id}/members`
List explicitly assigned members. **Manager/Admin only.**

---

### `POST /projects/{project_id}/members`
Assign member to private project. **Manager/Admin only.**
**Request:** `{ "user_id": "uuid" }`
**Errors:** `409 ALREADY_MEMBER`

---

### `DELETE /projects/{project_id}/members/{user_id}`
Remove member from project. **Manager/Admin only.**

---

## 10. Task Endpoints

### `GET /tasks`
List tasks for a project. **Any member.**
**Query:** `workspace_id` (required), `project_id` (required), `page`, `per_page`

---

### `POST /tasks`
Create task. **Manager/Admin only.**

| Field | Required | Validation |
|-------|----------|-----------|
| `project_id` | ✅ | Visible to caller |
| `name` | ✅ | 1–150 chars, unique in project |
| `assignee_user_id` | ❌ | Workspace member |
| `estimated_hours` | ❌ | > 0 |
| `billable_override` | ❌ | `null` = inherit from project |
| `hourly_rate` | ❌ | Decimal ≥ `"0.00"` |

---

### `GET /tasks/{task_id}`
Get single task. **Any member.**

---

### `PATCH /tasks/{task_id}`
Update task. **Manager/Admin only.** All fields optional except `project_id`.

---

### `DELETE /tasks/{task_id}`
Delete task. **Manager/Admin only.** Sets `task_id = NULL` on entries.

---

## 11. Tag Endpoints

### `GET /tags`
List workspace tags. **Any member.**
**Query:** `workspace_id` (required)

---

### `POST /tags`
Create tag. **Manager/Admin only.**
**Request:** `{ "name": "bug-fix", "color": "#EF4444" }`
**Errors:** `409 DUPLICATE_NAME`

---

### `PATCH /tags/{tag_id}`
Update tag. **Manager/Admin only.**
**Request (all optional):** `{ "name"?, "color"? }`

---

### `DELETE /tags/{tag_id}`
Delete tag. **Admin only.** Cascades to all entries via `time_entry_tags`.

---

## 12. Time Entry Endpoints

### `GET /time-entries/current`
Get currently running timer. Returns `null` if none.
**Query:** `workspace_id` (required)

**Success `200`:**
```json
{
  "data": {
    "id": "uuid",
    "project_id": "uuid",
    "project_name": "Website Redesign",
    "task_id": null,
    "description": "Working on homepage",
    "billable": true,
    "status": "running",
    "start_time": "2026-05-22T08:00:00+00:00",
    "elapsed_seconds": 3600,
    "tags": [],
    "hourly_rate": "75.00"
  }
}
```

---

### `POST /time-entries/start`
Start a new timer. **Member+ only.**
**Query:** `workspace_id` (required)

| Field | Required | Validation |
|-------|----------|-----------|
| `project_id` | ✅ | Visible to caller |
| `task_id` | ❌ | Must belong to project |
| `description` | ❌ | Max 500 chars. Required if `mandatory_description=true` |
| `billable` | ❌ | Defaults to project's `default_billable` |
| `tag_ids` | ❌ | Must belong to workspace |
| `force` | ❌ | Default `false`. If `true`, stops running timer first |

**Success `201`:** Returns `TimeEntryObject` with `status=running`.

**Business rules:**
- `force=false` and timer already running → `409 TIMER_ALREADY_RUNNING`
- `force=true` → stop running timer (rounding applied), start new one
- Rate snapshot taken at creation

**Errors:** `400 BAD_REQUEST`, `403 FORBIDDEN`, `404 NOT_FOUND`, `409 TIMER_ALREADY_RUNNING`

---

### `POST /time-entries/{entry_id}/stop`
Stop a running timer. Applies rounding.
**Auth:** Entry owner, Manager, or Admin.

**Request (all optional):**
```json
{ "idle_end_time": "2026-05-22T09:45:00+00:00" }
```

`idle_end_time`: When provided, duration computed as `idle_end_time - start_time`.

**Success `200`:**
```json
{
  "data": {
    "id": "uuid",
    "status": "draft",
    "start_time": "...",
    "end_time": "...",
    "duration_seconds": 3600,
    "hourly_rate": "75.00",
    "billable_amount": "75.00",
    "updated_at": "..."
  },
  "rounding": {
    "raw_seconds": 3780,
    "rounded_seconds": 3600,
    "rounding_mode": "down",
    "rounding_interval_minutes": 30
  }
}
```

**Errors:** `400 BAD_REQUEST` (not running), `403 FORBIDDEN`, `404 NOT_FOUND`

---

### `POST /time-entries/{entry_id}/continue` *(NEW — v1.1)*

Start a new timer pre-filled with the same project, task, description,
billable flag, and tags as the source entry.

**Auth:** Admin, Manager, or Member (own entries only for Member).
**Query:** `workspace_id` (required)
**Path:** `entry_id` (uuid) — the source entry to continue from

**Request body:**

| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| `force` | `boolean` | ❌ | Default `false`. If `true` and a timer is running, stops it first. |

```json
{ "force": false }
```

**Behavior:**
1. Fetch source entry. Verify it belongs to the workspace.
2. Verify caller has access (Member can only continue own entries;
   Manager/Admin can continue any).
3. Verify source entry status is NOT `pending`.
   If `status === 'pending'` → `400 CANNOT_CONTINUE_PENDING`.
4. If another timer is running and `force=false` → `409 TIMER_ALREADY_RUNNING`.
5. If another timer is running and `force=true` → stop it (rounding applied), then proceed.
6. Create new time entry with:
   - `project_id` = source `project_id`
   - `task_id` = source `task_id`
   - `description` = source `description`
   - `billable` = source `billable`
   - `tag_ids` = source entry's tags
   - `status` = `running`
   - `start_time` = NOW()
   - Fresh rate snapshot via `rate_service.resolve_rate()`
7. Return the new running entry.

**Success `201`:**
```json
{
  "data": {
    "id": "uuid",
    "workspace_id": "uuid",
    "user_id": "uuid",
    "project_id": "uuid",
    "project_name": "Website Redesign",
    "task_id": "uuid | null",
    "task_name": "string | null",
    "description": "Homepage wireframes",
    "billable": true,
    "status": "running",
    "start_time": "2026-05-26T09:00:00+00:00",
    "end_time": null,
    "duration_seconds": null,
    "tags": [],
    "hourly_rate": "75.00",
    "billable_amount": null,
    "created_at": "2026-05-26T09:00:00+00:00",
    "updated_at": "2026-05-26T09:00:00+00:00"
  },
  "source_entry_id": "uuid"
}
```

**Note:** `source_entry_id` is included so the frontend can optionally
highlight the source entry that was continued.

**Errors:**

| Status | Code | Condition |
|--------|------|-----------|
| `400` | `CANNOT_CONTINUE_PENDING` | Source entry status is `pending` |
| `403` | `FORBIDDEN` | Member attempting to continue another member's entry |
| `404` | `NOT_FOUND` | Source entry not found in workspace |
| `409` | `TIMER_ALREADY_RUNNING` | Another timer running and `force=false` |

---

### `POST /time-entries/{entry_id}/duplicate` *(NEW — v1.1)*

Create a new draft time entry copied from the source entry, dated to today.

**Auth:** Admin, Manager, or Member (own entries only for Member).
**Query:** `workspace_id` (required)
**Path:** `entry_id` (uuid) — the source entry to duplicate

**Request body:** None required.

**Behavior:**
1. Fetch source entry. Verify it belongs to the workspace.
2. Verify caller has access (Member can only duplicate own entries;
   Manager/Admin can duplicate any).
3. Verify source entry status is NOT `pending`.
   If `status === 'pending'` → `400 CANNOT_DUPLICATE_PENDING`.
4. Compute the new entry's times:
   - `start_time` = start of today in the workspace timezone (midnight UTC equivalent)
   - `end_time` = `start_time` + source `duration_seconds` (in seconds)
5. Apply rounding to the duration (same as any new entry creation).
6. Take a fresh rate snapshot via `rate_service.resolve_rate()`.
7. Compute and store `billable_amount_cents`.
8. Create and save the new entry with `status = 'draft'`.

**Success `201`:**
```json
{
  "data": { "<<TimeEntryObject>>" },
  "rounding": { "<<RoundingResult>>" },
  "source_entry_id": "uuid"
}
```

**`rounding`** is always included so the frontend can show the rounding toast.

**Errors:**

| Status | Code | Condition |
|--------|------|-----------|
| `400` | `CANNOT_DUPLICATE_PENDING` | Source entry status is `pending` |
| `403` | `FORBIDDEN` | Member attempting to duplicate another member's entry |
| `404` | `NOT_FOUND` | Source entry not found in workspace |

---

### `GET /time-entries`
List time entries. Cursor-paginated.
**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `workspace_id` | `uuid` | required | — |
| `cursor` | `string` | null | Opaque cursor from prev response |
| `limit` | `integer` | 50 | 1–200 |
| `user_id` | `uuid` | null | Members see only own |
| `project_id` | `uuid` | null | — |
| `client_id` | `uuid` | null | — |
| `status` | `string` | null | `draft\|running\|pending\|approved` |
| `billable` | `boolean` | null | — |
| `date_from` | `date` | null | `YYYY-MM-DD` |
| `date_to` | `date` | null | `YYYY-MM-DD` |
| `tag_ids` | `string` | null | Comma-separated UUIDs |

**Authorization:** Members see own entries only.

**Success `200`:**
```json
{
  "data": [ "<<TimeEntryObject>>" ],
  "next_cursor": "eyJ...",
  "limit": 50
}
```

---

### `POST /time-entries`
Create manual time entry. **Member+ only.**

| Field | Required | Validation |
|-------|----------|-----------|
| `project_id` | ✅ | Visible to caller |
| `task_id` | ❌ | Must belong to project |
| `start_time` | ✅ | ISO 8601. Before `end_time`. Within `past_entry_limit_days`. |
| `end_time` | ✅ | ISO 8601. After `start_time`. Not in future. |
| `description` | ❌ | Max 500 chars. Required if `mandatory_description=true` |
| `billable` | ❌ | Defaults to project's `default_billable` |
| `tag_ids` | ❌ | Must belong to workspace |

**Success `201`:**
```json
{
  "data": { "<<TimeEntryObject>>" },
  "rounding": { "<<RoundingResult>>" },
  "has_overlap": false
}
```

**Errors:** `400 PAST_ENTRY_LIMIT_EXCEEDED`, `400 BAD_REQUEST`, `403 FORBIDDEN`, `404 NOT_FOUND`

---

### `GET /time-entries/{entry_id}`
Get single entry. Members see own only; Managers/Admins see any.
**Query:** `workspace_id` (required)

---

### `PATCH /time-entries/{entry_id}`
Update entry. Respects lock rules.
**Query:** `workspace_id` (required)

**Request (all optional):** `project_id`, `task_id`, `start_time`, `end_time`, `description`, `billable`, `tag_ids`

**Lock rules:**
- `status = pending` or `status = approved` → `403 ENTRY_LOCKED` (non-Admins)
- Older than `lock_period_days` → `403 ENTRY_LOCKED` (non-Admins)
- Admins: never locked

**Re-rounding:** Applied fresh from new raw duration on every save.
**Rate re-snapshot:** Taken from current hierarchy on every edit.

**Success `200`:**
```json
{
  "data": { "<<TimeEntryObject>>" },
  "rounding": { "<<RoundingResult>>" }
}
```

---

### `DELETE /time-entries/{entry_id}`
Delete entry. Same lock rules as PATCH.
**Success `200`:** `{ "message": "Time entry deleted." }`
**Errors:** `403 ENTRY_LOCKED`, `403 FORBIDDEN`, `404 NOT_FOUND`

---

## 13. Approval Endpoints

All approval endpoints require `approval_workflow_enabled = true`.
If workflow disabled → `400 BAD_REQUEST`.

---

### `POST /approvals/submit`
Member submits week. Locks qualifying draft entries.
**Auth:** Member+
**Query:** `workspace_id` (required)
**Request:** `{ "week_start": "2026-05-18" }` (must be a Monday)

**Success `200`:**
```json
{
  "data": {
    "submission_id": "uuid",
    "week_start": "2026-05-18",
    "week_end": "2026-05-24",
    "status": "pending",
    "submitted_entries_count": 7,
    "skipped_approved_count": 2,
    "submitted_at": "2026-05-22T09:00:00+00:00"
  }
}
```

**Errors:** `400 NO_ENTRIES_TO_SUBMIT`, `400 INVALID_WEEK_START`, `409 ALREADY_SUBMITTED`

---

### `GET /approvals/pending`
List pending submissions. **Manager/Admin only.**
**Query:** `workspace_id`, `user_id?`, `page`, `per_page`

---

### `POST /approvals/{submission_id}/approve`
Approve submitted week. **Manager/Admin only.**

**Success `200`:**
```json
{
  "data": {
    "submission_id": "uuid",
    "status": "approved",
    "reviewed_by": { "user_id": "uuid", "full_name": "Alex Johnson" },
    "reviewed_at": "...",
    "entries_approved_count": 7
  }
}
```

**Errors:** `400 BAD_REQUEST`, `403 FORBIDDEN`, `404 NOT_FOUND`

---

### `POST /approvals/{submission_id}/reject`
Reject with mandatory note. **Manager/Admin only.**
**Request:** `{ "note": "Missing descriptions on Tuesday entries..." }`

**Success `200`:**
```json
{
  "data": {
    "submission_id": "uuid",
    "status": "rejected",
    "rejection_note": "...",
    "reviewed_by": { "user_id": "uuid", "full_name": "Alex Johnson" },
    "reviewed_at": "...",
    "entries_unlocked_count": 7
  }
}
```

**Errors:** `400 BAD_REQUEST`, `403 FORBIDDEN`, `404 NOT_FOUND`, `422 VALIDATION_ERROR`

---

## 14. Report Endpoints

All endpoints respect Viewer data isolation (§1.11).

---

### `GET /reports/summary`
Grouped summary of hours and amounts.
**Query params:**

| Param | Required | Validation | Description |
|-------|----------|-----------|-------------|
| `workspace_id` | ✅ | — | — |
| `group_by` | ✅ | `project\|user\|client\|tag` | Grouping dimension |
| `date_from` | ✅ | `YYYY-MM-DD` | Inclusive start |
| `date_to` | ✅ | `YYYY-MM-DD`, ≥ `date_from` | Inclusive end |
| `project_id` | ❌ | — | Filter by project |
| `client_id` | ❌ | — | Filter by client |
| `user_id` | ❌ | — | Members locked to own |
| `billable` | ❌ | — | Billable flag filter |
| `status` | ❌ | `draft\|pending\|approved` | Entry status filter |

**Success `200`:**
```json
{
  "data": [
    {
      "group_key": "uuid",
      "group_label": "Website Redesign",
      "total_seconds": 162000,
      "total_hours": 45.0,
      "billable_seconds": 144000,
      "billable_hours": 40.0,
      "non_billable_hours": 5.0,
      "total_billable_amount": "3000.00",
      "entry_count": 22
    }
  ],
  "summary": {
    "total_hours": 45.0,
    "total_billable_amount": "3000.00",
    "date_from": "2026-05-01",
    "date_to": "2026-05-31"
  }
}
```

---

### `GET /reports/detailed`
Cursor-paginated entry list with filters.
**Query:** Same as summary + `cursor`, `limit`, `sort_by`, `sort_order`, `tag_ids`

**Success `200`:**
```json
{
  "data": [ "<<TimeEntryObject>>" ],
  "next_cursor": "eyJ...",
  "limit": 50,
  "summary": { "total_hours": 45.0, "total_billable_amount": "3000.00" }
}
```

---

### `GET /reports/weekly` *(NEW — v1.1)*

Per-user, per-day breakdown of hours for a selected date range.

**Auth:** Any workspace member.
**Query:** `workspace_id` (required)

**Query parameters:**

| Param | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|-----------|-------------|
| `workspace_id` | `uuid` | ✅ | — | — | — |
| `date_from` | `date` | ✅ | — | `YYYY-MM-DD`, Monday | Start of range (must be Monday for week alignment) |
| `date_to` | `date` | ✅ | — | `YYYY-MM-DD`, ≥ `date_from`, max 31 days span | End of range |
| `user_id` | `uuid` | ❌ | `null` | — | Filter to single user. Members/Viewers: auto-locked to own ID. |
| `project_id` | `uuid` | ❌ | `null` | — | Filter by project |
| `billable` | `boolean` | ❌ | `null` | — | Filter by billable flag |

**Authorization:**
- Admins and Managers: see all workspace members' rows.
- Members: `user_id` is automatically locked to their own ID. Any supplied `user_id`
  that is not their own returns `403 FORBIDDEN`.
- Viewers: same as Members — own row only.

**Success `200`:**
```json
{
  "data": {
    "date_from": "2026-05-18",
    "date_to": "2026-05-24",
    "days": ["2026-05-18", "2026-05-19", "2026-05-20", "2026-05-21", "2026-05-22", "2026-05-23", "2026-05-24"],
    "rows": [
      {
        "user_id": "uuid",
        "user_name": "Sam Lee",
        "avatar_url": "string | null",
        "total_seconds": 138600,
        "total_hours": 38.5,
        "billable_hours": 32.0,
        "total_billable_amount": "2400.00",
        "days": {
          "2026-05-18": {
            "total_seconds": 28800,
            "total_hours": 8.0,
            "billable_hours": 8.0,
            "entry_count": 3
          },
          "2026-05-19": {
            "total_seconds": 21600,
            "total_hours": 6.0,
            "billable_hours": 4.5,
            "entry_count": 2
          },
          "2026-05-20": {
            "total_seconds": 0,
            "total_hours": 0.0,
            "billable_hours": 0.0,
            "entry_count": 0
          }
        }
      }
    ],
    "totals": {
      "by_day": {
        "2026-05-18": { "total_hours": 24.0, "billable_hours": 20.0 },
        "2026-05-19": { "total_hours": 18.5, "billable_hours": 16.0 }
      },
      "grand_total_hours": 192.5,
      "grand_total_billable_amount": "14437.50"
    }
  }
}
```

**Viewer data isolation:**
- `total_billable_amount` (row level and totals level) absent for Viewer role.
- `billable_hours` absent for Viewer role.
- `grand_total_billable_amount` absent for Viewer role.

**Cell popover data:** To get individual entries for a specific user+day cell,
use `GET /time-entries` with `user_id`, `date_from`, and `date_to` set to that
specific day. No separate endpoint is needed.

**Errors:**

| Status | Code | Condition |
|--------|------|-----------|
| `400` | `BAD_REQUEST` | `date_to < date_from` or span > 31 days |
| `403` | `FORBIDDEN` | Member/Viewer supplying another user's `user_id` |
| `422` | `VALIDATION_ERROR` | Invalid date format |

---

### `GET /reports/summary/export`
CSV download of summary report. Same query params as `GET /reports/summary`.

**Response:** `200 OK` with:
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="yusitime_summary_2026-05-01_2026-05-31.csv"
```

CSV columns (Viewer excludes financial):
```
Group,Total Hours,Billable Hours,Non-Billable Hours,Billable Amount,Entry Count
```

---

### `GET /reports/detailed/export`
CSV download of detailed report. Same query params as `GET /reports/detailed`.

CSV columns (Viewer excludes financial):
```
Date,User,Project,Client,Task,Description,Start Time,End Time,Duration (h),Billable,Hourly Rate,Billable Amount,Tags,Status
```

---

### `GET /reports/weekly/export` *(NEW — v1.1)*

CSV download of weekly report. Same query params as `GET /reports/weekly`.

**Response:** `200 OK` with:
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="yusitime_weekly_2026-05-18_2026-05-24.csv"
```

CSV columns (Viewer excludes financial):
```
Member,Mon 18,Tue 19,Wed 20,Thu 21,Fri 22,Sat 23,Sun 24,Total Hours,Billable Amount
```

One row per member. Hours displayed as decimal (e.g., `8.0`, `0.0`).
Financial column absent for Viewer role.

---

### `GET /reports/saved-views`
List saved views for current user.
**Query:** `workspace_id` (required)

---

### `POST /reports/saved-views`
Save a filter configuration.
**Request:** `{ "name", "report_type": "summary|detailed|weekly", "filters": {} }`
**Note:** `report_type` now accepts `"weekly"` as a valid value (updated in v1.1).
**Errors:** `409 DUPLICATE_NAME`

---

### `DELETE /reports/saved-views/{view_id}`
Delete a saved view.
**Query:** `workspace_id` (required)
**Errors:** `404 NOT_FOUND`

---

## 15. Webhook Endpoints

All webhook endpoints are **Admin only**.

### `GET /webhooks`
List webhooks. Note: `secret` value never returned (`has_secret: boolean` instead).

---

### `POST /webhooks`
Register webhook.
**Request:**
```json
{
  "url": "https://hooks.example.com/yusitime",
  "subscribed_events": ["timesheet.submitted", "timesheet.approved"],
  "secret": "mysecretkey123"
}
```

**Validation:** URL must start with `https://`. `subscribed_events` non-empty.
**Retry policy:** 3 attempts: 5s → 25s → 125s backoff.
**Signing:** `X-Yusitime-Signature: sha256=<hmac-hex>` if secret set.

---

### `PATCH /webhooks/{webhook_id}`
Update URL, events, secret, or active status. All fields optional.

---

### `DELETE /webhooks/{webhook_id}`
Unregister webhook. Cascades to delivery logs.

---

### `GET /webhooks/{webhook_id}/deliveries`
View delivery attempts. **Admin only.**
**Query:** `workspace_id`, `page`, `per_page`

---

## 16. Notification Endpoints

### `GET /notifications`
List notifications for current user.
**Query:** `workspace_id`, `unread_only` (default false), `page`, `per_page`

---

### `POST /notifications/read`
Mark specific notifications read.
**Request:** `{ "ids": ["uuid1", "uuid2"] }`

---

### `POST /notifications/read-all`
Mark all notifications read.
**Query:** `workspace_id`

---

## 17. Appendix A — Enum Values Reference

| Enum | Valid Values |
|------|-------------|
| `workspace_role` | `admin`, `manager`, `member`, `viewer` |
| `project_visibility` | `public`, `private` |
| `project_status` | `active`, `archived` |
| `entry_status` | `draft`, `running`, `pending`, `approved` |
| `submission_status` | `pending`, `approved`, `rejected` |
| `rounding_mode` | `none`, `nearest`, `up`, `down` |
| `rounding_interval_minutes` | `1`, `5`, `6`, `10`, `15`, `30` |
| `idle_timeout_minutes` | `1`, `2`, `5`, `10`, `15` |
| `webhook_event_type` | `time_entry.created`, `time_entry.updated`, `timesheet.submitted`, `timesheet.approved`, `timesheet.rejected` |
| `notification_event_type` | `timesheet_submitted`, `timesheet_approved`, `timesheet_rejected`, `timer_auto_stopped`, `workspace_deleted` |
| `audit_action` | `create`, `update`, `delete`, `approve`, `reject`, `submit`, `lock_override`, `role_change`, `invite_generated`, `invite_revoked`, `workspace_soft_deleted` |
| `webhook_delivery_status` | `success`, `failed`, `retrying` |
| `report_type` (saved views) | `summary`, `detailed`, `weekly` |

---

## 18. Appendix B — Endpoint Summary Table

| Method | Path | Auth | Min Role | Description |
|--------|------|------|----------|-------------|
| POST | `/auth/signup` | No | — | Register new user |
| POST | `/auth/login` | No | — | Login |
| POST | `/auth/refresh` | Cookie | — | Refresh access token |
| POST | `/auth/logout` | Yes | any | Logout |
| GET | `/auth/google` | No | — | Start Google OAuth |
| GET | `/auth/google/callback` | No | — | Google OAuth callback |
| POST | `/auth/forgot-password` | No | — | Request password reset |
| POST | `/auth/reset-password` | No | — | Consume reset token |
| GET | `/users/me` | Yes | any | Get own profile |
| PATCH | `/users/me` | Yes | any | Update own profile |
| DELETE | `/users/me` | Yes | any | Anonymize own account |
| GET | `/workspaces` | Yes | any | List my workspaces |
| POST | `/workspaces` | Yes | any | Create workspace |
| GET | `/workspaces/{id}` | Yes | any member | Get workspace details |
| PATCH | `/workspaces/{id}` | Yes | admin | Update workspace settings |
| DELETE | `/workspaces/{id}` | Yes | admin | Soft-delete workspace |
| GET | `/workspaces/{id}/members` | Yes | any member | List members |
| PATCH | `/workspaces/{id}/members/{uid}` | Yes | admin | Change member role |
| DELETE | `/workspaces/{id}/members/{uid}` | Yes | admin | Remove member |
| POST | `/workspaces/{id}/invites` | Yes | admin | Generate invite link |
| GET | `/workspaces/{id}/invites` | Yes | admin | List pending invites |
| DELETE | `/workspaces/{id}/invites/{token}` | Yes | admin | Revoke invite link |
| GET | `/invites/{token}` | No | — | Validate invite token |
| POST | `/invites/{token}/accept` | Yes | any | Accept invite |
| GET | `/clients` | Yes | any member | List clients |
| POST | `/clients` | Yes | manager+ | Create client |
| GET | `/clients/{id}` | Yes | any member | Get client |
| PATCH | `/clients/{id}` | Yes | manager+ | Update client |
| DELETE | `/clients/{id}` | Yes | admin | Delete client |
| GET | `/projects` | Yes | any member | List visible projects |
| POST | `/projects` | Yes | manager+ | Create project |
| GET | `/projects/{id}` | Yes | any member | Get project |
| PATCH | `/projects/{id}` | Yes | manager+ | Update project |
| POST | `/projects/{id}/archive` | Yes | manager+ | Archive project |
| DELETE | `/projects/{id}` | Yes | admin | Delete project |
| GET | `/projects/{id}/members` | Yes | manager+ | List project members |
| POST | `/projects/{id}/members` | Yes | manager+ | Assign member |
| DELETE | `/projects/{id}/members/{uid}` | Yes | manager+ | Remove member |
| GET | `/tasks` | Yes | any member | List tasks |
| POST | `/tasks` | Yes | manager+ | Create task |
| GET | `/tasks/{id}` | Yes | any member | Get task |
| PATCH | `/tasks/{id}` | Yes | manager+ | Update task |
| DELETE | `/tasks/{id}` | Yes | manager+ | Delete task |
| GET | `/tags` | Yes | any member | List tags |
| POST | `/tags` | Yes | manager+ | Create tag |
| PATCH | `/tags/{id}` | Yes | manager+ | Update tag |
| DELETE | `/tags/{id}` | Yes | admin | Delete tag |
| GET | `/time-entries/current` | Yes | any member | Get running timer |
| POST | `/time-entries/start` | Yes | member+ | Start timer |
| POST | `/time-entries/{id}/stop` | Yes | member+ | Stop timer |
| POST | `/time-entries/{id}/continue` | Yes | member+ | **NEW** Continue entry as new timer |
| POST | `/time-entries/{id}/duplicate` | Yes | member+ | **NEW** Duplicate entry to today |
| GET | `/time-entries` | Yes | any member | List entries |
| POST | `/time-entries` | Yes | member+ | Create manual entry |
| GET | `/time-entries/{id}` | Yes | any member | Get entry |
| PATCH | `/time-entries/{id}` | Yes | member+ | Update entry |
| DELETE | `/time-entries/{id}` | Yes | member+ | Delete entry |
| POST | `/approvals/submit` | Yes | member+ | Submit week |
| GET | `/approvals/pending` | Yes | manager+ | List pending submissions |
| POST | `/approvals/{id}/approve` | Yes | manager+ | Approve submission |
| POST | `/approvals/{id}/reject` | Yes | manager+ | Reject submission |
| GET | `/reports/summary` | Yes | any member | Summary report |
| GET | `/reports/detailed` | Yes | any member | Detailed report |
| GET | `/reports/weekly` | Yes | any member | **NEW** Weekly per-user-per-day report |
| GET | `/reports/summary/export` | Yes | any member | Export summary CSV |
| GET | `/reports/detailed/export` | Yes | any member | Export detailed CSV |
| GET | `/reports/weekly/export` | Yes | any member | **NEW** Export weekly CSV |
| GET | `/reports/saved-views` | Yes | any member | List saved views |
| POST | `/reports/saved-views` | Yes | any member | Save a report view |
| DELETE | `/reports/saved-views/{id}` | Yes | any member | Delete saved view |
| GET | `/webhooks` | Yes | admin | List webhooks |
| POST | `/webhooks` | Yes | admin | Register webhook |
| PATCH | `/webhooks/{id}` | Yes | admin | Update webhook |
| DELETE | `/webhooks/{id}` | Yes | admin | Delete webhook |
| GET | `/webhooks/{id}/deliveries` | Yes | admin | View delivery logs |
| GET | `/notifications` | Yes | any member | List notifications |
| POST | `/notifications/read` | Yes | any member | Mark as read |
| POST | `/notifications/read-all` | Yes | any member | Mark all as read |

**Total endpoints: 76** (was 73 in v1.0 — 3 new endpoints added)
