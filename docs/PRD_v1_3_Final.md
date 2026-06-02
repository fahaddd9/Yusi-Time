# Product Requirements Document (PRD) – Yusi Time MVP
**Version:** 1.3 (Final — 5 Clockify-Gap Features Added)
**Date:** 2026-05-26
**Status:** Finalized ✅
**Author:** Yusi Time Project Team
**Current Version: 1.4** (file named v1.3 for historical continuity)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-01 | Initial draft |
| 1.1 | 2026-05-22 | Post-anomaly review; idle detection, invite flow, rounding UX resolved |
| 1.2 | 2026-05-22 | **Final** — 6 ambiguities resolved: Manager invite permissions, Submit Week scope, re-rounding on edit, invite link expiry, approval toggle transition behavior, author field |
| 1.3 | 2026-05-26 | **5 Clockify-gap features added**: Continue entry, Duplicate entry, Description draft auto-save, Dashboard quick-continue, Weekly Report. PRD §3.3, §3.8, §5, §6, §7, §9, §10 updated. |
| 1.4 | 2026-05-31 | **Super Admin added**: Platform-level operator role documented in §4, §5, §6, §9, §10. Full UI roadmap added to §3.12. Out-of-scope section updated. |

---

## Table of Contents
1. [Product Overview](#1-product-overview)
2. [User Personas](#2-user-personas)
3. [Core Features & Requirements](#3-core-features--requirements)
   - [3.1 Workspace & User Management](#31-workspace--user-management)
   - [3.2 Authentication](#32-authentication)
   - [3.3 Time Tracking](#33-time-tracking)
   - [3.4 Idle Detection (Auto-Pause)](#34-idle-detection-auto-pause)
   - [3.5 Project & Task Organization](#35-project--task-organization)
   - [3.6 Timesheet Compliance](#36-timesheet-compliance)
   - [3.7 Billable Rates & Amounts](#37-billable-rates--amounts)
   - [3.8 Reporting & Analytics](#38-reporting--analytics)
   - [3.9 API, Webhooks & Integrations](#39-api-webhooks--integrations)
   - [3.10 Notifications](#310-notifications)
   - [3.11 Settings & Configuration](#311-settings--configuration)
   - [3.12 Super Admin Dashboard](#312-super-admin-dashboard)
4. [User Permissions & Roles](#4-user-permissions--roles)
5. [Business Rules & Validation Logic](#5-business-rules--validation-logic)
6. [User Stories (Key Flows)](#6-user-stories-key-flows)
7. [Design & UX Requirements (High-Level)](#7-design--ux-requirements-high-level)
8. [Assumptions & Constraints](#8-assumptions--constraints)
9. [Out of Scope for MVP](#9-out-of-scope-for-mvp)
10. [Acceptance Criteria Overview](#10-acceptance-criteria-overview)
11. [Glossary](#11-glossary)

---

## 1. Product Overview

**Yusi Time** is a time tracking application inspired by Clockify's ease of use and Odoo Timesheets' business compliance. The MVP delivers a standalone, web-first platform for individuals, teams, and agencies to log work hours, manage projects, ensure data integrity through locking and approvals, and prepare billable data — all without requiring a full ERP.

### Core Value Proposition
- **Effortless time capture** via a one-click timer, manual entry, weekly grid, quick-continue from past entries, and entry duplication.
- **Trustworthy records** thanks to timesheet locking, an approval workflow with a "submit-then-lock" mechanism, and full audit trails.
- **Transparent billing** with cascading hourly rates, billable flags, and invoice-ready reports.
- **Privacy-friendly productivity** — per-device idle detection that gives users full control over what gets recorded.
- **Zero data loss** — description drafts are auto-saved locally so users never lose work in progress.

---

## 2. User Personas

1. **Freelancer (Member)**
   - Needs fast, distraction-free tracking for multiple clients.
   - Relies on billable rates and summary reports for invoicing.
   - Values idle detection to avoid phantom time and rounding clarity.
   - Uses Continue and Duplicate buttons to restart recurring daily work with one click.

2. **Agency Owner (Admin)**
   - Oversees multiple workspaces, sets policies (lock dates, approvals).
   - Demands data integrity — timesheets must be immutable once submitted.
   - Requires visibility into billable vs non-billable hours across all projects.
   - Uses the Weekly Report to see team hours by person per day at a glance.

3. **Team Lead (Manager)**
   - Manages projects, assigns tasks, and reviews timesheets.
   - Needs to see team hours and approve/reject weeks quickly.
   - Wants to avoid race conditions where members change hours during review.

4. **Client / External Stakeholder (Viewer)**
   - Invited to view progress on specific (even private) projects.
   - Sees **only hours and descriptive data** — never financial figures.
   - No ability to edit or view rates.

---

## 3. Core Features & Requirements

### 3.1 Workspace & User Management

- **Workspace** = isolated container for projects, members, settings, and data. Users can belong to multiple workspaces.
- **Roles**: Admin, Manager, Member, Viewer (see Section 4).
- **Auto-creation on signup**: A default workspace `[User Name]'s Workspace` is created with the new user as Admin.

#### Inviting New Users
- **Only Admins** can invite new users to a workspace. Managers do not have invitation privileges.
- The Admin initiates an invitation by entering the invitee's email address and selecting a role (Manager, Member, or Viewer).
- **Because we do not send emails in MVP**, the system immediately generates a **shareable invite link** (e.g., `https://yusitime.com/join/abc123`). This link is displayed to the Admin, who copies and pastes it to the invitee via any external channel (Slack, WhatsApp, their own email).
- The link encodes the workspace ID and the pre-assigned role.
- **Invite link expiry**: Each generated link expires after **7 days** from the moment of creation. This value is a fixed system default in MVP (not configurable per workspace). After expiry, the link returns an error page and the Admin must generate a new one.
- On first visit, the invitee creates an account (or logs in if they already have one) and is automatically added to the workspace with the given role.
- No in-app notification is sent to the invitee until after they join. The Admin sees a success message with the copyable link and its expiry date displayed.
- An Admin can view and revoke pending (unused, non-expired) invite links from the Members settings page.

#### Workspace Deletion
- Admin can soft-delete a workspace. A confirmation modal is required.
- Data is retained for 30 days; restoration is possible within that window.
- After 30 days, the workspace and all its data are permanently deleted.
- All members receive an in-app notification upon workspace deletion.

#### User Account Deletion
- Blocked if the user is the sole Admin of any active workspace.
- Otherwise: remove from all workspaces and anonymize the record:
  - `name` → `Deleted User [short-UUID]`
  - `email` → `deleted-[short-UUID]@anonymous.local`
  - `google_id` → `NULL`
- Time entries and audit logs remain attributed to the anonymized user ID, preserving historical data integrity.

---

### 3.2 Authentication

- **Methods**: Email + password (Argon2 hashed) and "Sign in with Google" (OAuth2).
- **Email verification**: Not required for MVP.
- **Password reset**: Via email link (mandatory). Link expires after 1 hour. This is the **only** transactional email in MVP; integration with AWS SES is required.
- **Sessions**: JWT access/refresh tokens. Access token expires in 30 minutes; refresh token expires in 7 days.
- **Google OAuth**: First-time users automatically get a new account. No separate account-linking flow required for MVP.
- **Password rules**: Minimum 8 characters. No complexity requirements enforced.

---

### 3.3 Time Tracking

#### 3.3.1 One-Click Timer
- Startable from the Dashboard, Project Detail page, or a persistent global "Start Timer" button in the navigation.
- **Project/task switching while running**: Changing project or task automatically saves the elapsed time as a completed entry and immediately starts a new timer under the new selection, seamlessly.
- **Max duration**: Configurable per workspace (default 24 hours). When exceeded, the timer auto-stops and an in-app notification is sent to the user.
- **One active timer per user per workspace**: Starting a new timer while one is running presents a prompt to stop the previous one first.
- **Server-side state**: The timer's start timestamp is stored on the server. The frontend computes elapsed time from the server timestamp, synced at regular intervals. The timer survives page refreshes and browser restarts.
- **Stop behavior**: On stop, the raw duration is recorded and **immediately rounded** server-side according to the workspace rounding rule (see 3.3.4). The UI displays a clear confirmation message showing the rounded result.

#### 3.3.2 Continue Entry (NEW — v1.3)
- Every completed time entry (status = `draft` or `approved`) displays a **Continue (▶)** button.
- Clicking Continue starts a new timer immediately with the **same project, task, description, billable flag, and tags** as the source entry.
- **Lock rule**: Continue is available on `draft` and `approved` entries. Continue is **not available** on `pending` entries (locked, awaiting approval), because this would start a new timer implying the work is ongoing — which conflicts with the submitted state. Attempting to continue a pending entry returns a `403 FORBIDDEN`.
- **Timer conflict**: If a timer is already running when Continue is clicked, the standard conflict prompt appears ("Stop current timer and continue this entry?"). With user confirmation, the running timer is stopped (with rounding) and the new Continue timer starts.
- **Rate snapshot**: A fresh rate snapshot is taken for the new entry at the moment Continue is called, following the standard rate hierarchy. The new entry does NOT inherit the rate from the source entry.
- The Continue action creates a brand-new time entry record. It does not modify the source entry in any way.
- Continue is available from: the time entry list on the Dashboard, the Timesheet grid row actions, and the Detailed Report.

#### 3.3.3 Manual Time Entry
- **Fields**: Start/end datetime (or duration in H:MM format), project (mandatory), task (optional), description, tags, billable flag.
- Past entries are allowed up to a configurable limit (workspace setting, default 7 days back from today).
- **Overlap handling**: Overlapping entries are permitted. A soft inline warning appears if the new entry's time range overlaps any existing entry for the same user. The user may proceed despite the warning.

#### 3.3.4 Duplicate Entry (NEW — v1.3)
- Every completed time entry (status = `draft` or `approved`) displays a **Duplicate** action in its three-dot context menu.
- Duplicating an entry creates a **new draft entry** with the same project, task, description, billable flag, and tags as the source entry, but with:
  - `start_time` = beginning of the current day (midnight in workspace timezone)
  - `end_time` = `start_time` + source entry's `duration_seconds`
  - `status` = `draft`
  - A fresh rate snapshot is taken (same as any new entry creation)
- The new entry is saved immediately (no confirmation dialog). The standard rounding toast appears after save.
- **Lock rule**: Duplicate is available on `draft` and `approved` entries. Duplicate is **not available** on `pending` entries for the same reason as Continue — it would create confusion about which entries belong to which submission cycle.
- The source entry is not modified in any way.
- Duplicate is available from: the time entry list on the Dashboard, the Timesheet grid row actions, and the Detailed Report.

#### 3.3.5 Description Draft Auto-Save (NEW — v1.3)
- When a user types in the **description field of the TimerBar** (the persistent global timer input), the description text is **automatically saved to browser localStorage** as the user types.
- The draft key is scoped per user per workspace: `yt_desc_draft_{userId}_{workspaceId}`.
- On page load or refresh, if a draft exists in localStorage and no timer is currently running, the draft text is restored into the description field automatically.
- If a timer is currently running on load/refresh, the running timer's saved description (from the server) takes priority and the localStorage draft is cleared.
- The localStorage draft is **cleared** when:
  - The user successfully starts or stops a timer (entry is committed to the server).
  - The user explicitly clears the description field.
- This feature is **frontend-only** — no backend API or database change is required. It protects users from losing typed descriptions due to accidental page refresh or browser restart.
- The auto-save operates silently with no UI indicator — it is invisible infrastructure.

#### 3.3.6 Calendar / Grid View
- **Weekly timesheet grid**: Rows = projects/tasks, Columns = Mon–Sun. Each cell shows the total hours logged for that project on that day.
- Clicking a cell opens an inline form to log time for that project/day combination.
- **Overtime/budget warnings**: Visual indicators (color change, icon) appear when the daily total or project budget threshold is approached or exceeded.
- **Submit Week button**: Visible only when the workspace approval workflow is enabled. Disabled if there are no unlocked/unapproved entries in the current week. Submitted cells display a "Submitted" badge.

#### 3.3.7 Time Rounding & UI Communication
- **Workspace setting**: A single rounding rule applies workspace-wide, enforced server-side on every save operation.
- **Available options**: None, Round to nearest / Round up / Round down — to X minutes, where X ∈ {1, 5, 6, 10, 15, 30}.
- **On every save (new entry or edit)**: Rounding is applied from the raw input value. Whether this is a new timer stop or an edit to an existing entry, the system always rounds from the newly submitted raw duration.
- **Critical UX requirement**: After any save, the frontend must explicitly display the rounded result in a non-blocking toast notification.
  - Example: *"Timer stopped at 1h 3m. Saved as 1h 15m (rounded up to nearest 15 min)."*
  - For manual entries, a preview of the rounded duration is shown inline before the user confirms saving.
- **Rounding is irreversible per save**: The original raw seconds are not stored. Each save computes rounding fresh from whatever raw value was submitted for that operation.

---

### 3.4 Idle Detection (Auto-Pause)

- **Workspace toggle** (Admin only): Enable "Auto-pause after inactivity".
- **Configurable timeout**: 1, 2, 5, 10, or 15 minutes of inactivity before idle state is triggered.
- **Behavior**:
  1. Timer is running; user stops interacting (mouse, keyboard, touch) for the configured timeout duration.
  2. Timer **continues counting**, but a secondary label appears alongside it: **"Idle: X min"**.
  3. When the user returns, a modal prompt appears with **three options** (no auto-dismiss; must be actively chosen):
     - **Keep Time & Continue**: Idle time is retained as normal work time. Timer continues running from its current value.
     - **Discard Idle Time & Stop Timer**: The timer is retroactively stopped at the moment idle began. The entry is saved ending at that point, without the idle period.
     - **Discard Idle Time & Continue**: The current entry is split at the moment idle began. The idle period is discarded. A **new timer automatically starts** from the moment the user returned, so work continues without manual restart.
  4. If the user manually stops the timer while in idle state, the same three-option modal appears before the entry is finalized.
- **Cross-device behavior**: Idle detection is strictly per-device. There is no cross-device sync of idle state. A user working on two devices simultaneously will see independent idle prompts on each.

---

### 3.5 Project & Task Organization

#### Hierarchy
`Client (optional) → Project → Task`

#### Client
- Fields: Name, optional contact info (phone, email — for reference only, not used by the system).
- Purpose: Grouping and reporting. Has no functional logic beyond organization.

#### Project
- **Fields**: Name, client (optional), default billable flag, hourly budget (in hours or cost), visibility, status.
- **Visibility**:
  - **Public**: Visible to all workspace members of any role.
  - **Private**: Visible only to explicitly assigned members (of any role) plus all Managers and Admins automatically.
  - **Viewers**: Can be explicitly assigned to private projects. They will see only hours and task descriptions — never financial fields.
- **Status**: Active or Archived. Archived projects are hidden from timer dropdowns but remain visible in reports.

#### Task
- Optional sub-entity under a project.
- Fields: Name, assignee (single workspace member), estimated hours, billable flag override (overrides project default).
- Tasks with an assignee are visible to that assignee even on private projects.

#### Tags
- Free-form labels applied to individual time entries.
- Managed at workspace level; reusable across projects.

#### Description
- Free-text field on each time entry.
- Can be made mandatory workspace-wide via workspace settings (Admin toggle).

---

### 3.6 Timesheet Compliance

#### 3.6.1 Locking (Immutable Records)

- Admin sets a **rolling lock period** in days (e.g., 7). Entries older than `(today − lock_days)` become **read-only** for non-Admin roles.
- **When approvals are disabled**: The rolling lock date applies to **all entries** in the workspace, regardless of status.
- **When approvals are enabled**: The rolling lock date applies **only to Approved entries**. Unapproved/unlocked entries remain editable by the member even if they fall within the lock window. Submitted-but-pending entries are separately locked to the member by the submission mechanism (see 3.6.2), not by the lock date.
- **Admins are never blocked** by the lock date. They can override and edit any entry at any time.

#### Approval Toggle Transition Behavior
When an Admin **disables** the approval workflow on a workspace that already has entries in various states:
- **Approved entries**: Immediately fall under the rolling lock date rule. If they are older than the lock window, they become read-only to non-Admins.
- **Pending (submitted but not yet reviewed) entries**: Remain locked to the member until an Admin or Manager explicitly approves or rejects them, or an Admin manually unlocks them. They do not become freely editable just because approvals were toggled off.
- **Unlocked/unapproved entries**: Immediately fall under the rolling lock date rule going forward. New entries created after the toggle follow date-based locking only.
- When an Admin **re-enables** the approval workflow, prior date-locked entries are not affected; the workflow applies to new submissions going forward.

#### 3.6.2 Approval Workflow (Submit-then-Lock)

- **Workspace toggle** (Admin only): "Timesheet Approval" — off by default.
- A **timesheet** = the collection of a user's time entries for a given calendar week (Monday–Sunday). Approved entries from prior cycles in the same week are excluded from new submissions.

**Submission process**:
1. Member clicks **"Submit Week"** in the weekly grid view.
2. A confirmation dialog lists exactly which entries will be submitted: **only entries that are currently unlocked and unapproved** (entries already Approved in that week are skipped — they are not re-submitted).
3. On confirmation, all included entries become **locked to the member** (they cannot edit or delete them). The timesheet status becomes **Pending**.
4. Managers and Admins see the submitted week in the Approvals dashboard with a "Pending" badge.

**Review**:
- **Approve**: Manager or Admin approves (bulk week approval). Entries remain locked and are now marked **Approved**. They subsequently fall under the rolling lock date rule like any other approved entry.
- **Reject**: Manager or Admin rejects with a **mandatory rejection note**. All entries in that submission revert to **Unlocked/Editable** status. The member receives an in-app notification with the rejection note and can modify and resubmit.

**Partial rejection** (MVP scope): Rejection operates at the **whole-week submission level** in MVP. Individual entry rejection is a post-MVP enhancement.

---

### 3.7 Billable Rates & Amounts

- **Currency**: One currency per workspace, default USD, selectable from a predefined ISO currency list.
- **Hourly rate inheritance hierarchy**: Workspace default → Client → Project → Task. The most specific rate defined wins.
- **Rate snapshot**: At the moment a time entry is created or saved, the effective rate is fetched from the hierarchy and stored directly on the entry. Subsequent changes to rates at any level do not retroactively affect existing entries.
- **Billable amount** = (rounded duration in hours) × snapshotted hourly rate.
- **Invoice-ready data**: Reports display billable amounts grouped by client, project, or member. No invoicing engine (PDF generation, sending) exists in MVP.

---

### 3.8 Reporting & Analytics

#### Dashboard Widgets
- Running timer with elapsed time.
- Today's total logged hours.
- Weekly goal progress bar.
- Top projects by hours this week.
- Quick action buttons: Start Timer, Add Manual Entry, View Reports.
- **Recent entries list with Continue and Duplicate actions** (NEW — v1.3): The last 5 time entries shown on the Dashboard each display a Continue (▶) button for one-click restart, and a Duplicate action in the three-dot menu.

#### Summary Report
- Groupable by: Project, User, Client.
- Shows: Total hours, billable hours, non-billable hours, billable amount (hidden from Viewers).
- Visualization: Bar chart by selected grouping.
- Export: CSV.

#### Detailed Report
- Paginated list of individual time entries.
- Sortable and filterable by: date range, project, user, client, billable flag, tags.
- Export: CSV.
- Viewers see: hours, description, project, task, tags only — no rates or amounts.
- **Continue and Duplicate actions available per entry row** (NEW — v1.3): Each entry row in the Detailed Report exposes the Continue (▶) button and the Duplicate option in the three-dot context menu, subject to the same lock rules as described in §3.3.2 and §3.3.4.

#### Weekly Report (NEW — v1.3)
- A dedicated report page (`/reports/weekly`) showing a per-user, per-day breakdown of hours for a selected date range.
- **Layout**: Rows = workspace members (filterable). Columns = days within the selected week or custom date range. Cells = total hours logged by that user on that day.
- **Filters**: Date range (defaults to current week), user filter (Admins/Managers see all members; Members see only themselves), project filter (optional), billable filter (optional).
- **Cell data**: Total hours logged (all statuses combined). Clicking a cell shows a popover listing the individual entries for that user on that day.
- **Summary row**: Totals per day and grand total for the week.
- **Summary column**: Total hours per user for the selected range.
- **Billable/non-billable split**: Optional toggle to split cell display into billable + non-billable sub-values.
- **Export**: CSV export with one row per user per day.
- **Viewer access**: Viewers see only their own row (single-user view). Financial amounts absent.
- **Member access**: Members see only their own row. Same restriction as Summary/Detailed reports.

#### Project Budget Status
- Progress bar showing logged billable hours or cost against the project budget.
- Visual warning when budget is at 80% and 100%.

#### Saved Report Views
- Users can save their current filter configuration as a named view, private to their account.
- Saved views are listed in a sidebar for quick access.
- Weekly Report supports saved views with the same mechanism.

---

### 3.9 API, Webhooks & Integrations

- **RESTful API v1**, documented via OpenAPI 3.1 specification.
- **Authentication**: OAuth2 / JWT. All endpoints require a valid access token.
- All core CRUD operations for time entries, projects, clients, tasks, and members are exposed via the API.

**Webhooks** — events emitted:
- `time_entry.created`
- `time_entry.updated`
- `timesheet.submitted`
- `timesheet.approved`
- `timesheet.rejected`

Webhook delivery includes simple retry logic (3 attempts with exponential backoff). No pre-built third-party integrations in MVP; the ecosystem is built via API + webhooks.

---

### 3.10 Notifications

- **In-app notification center**: Bell icon in the navigation bar with an unread badge count.
- Notifications are workspace-scoped.

**Notification events**:

| Event | Recipient |
|-------|-----------|
| Timesheet submitted by member | All Managers and Admins in workspace |
| Timesheet approved | The submitting Member |
| Timesheet rejected (includes rejection note) | The submitting Member |
| Timer auto-stopped (max duration exceeded) | The Member whose timer stopped |
| Workspace soft-deleted | All workspace members |

**Invitation notifications**: No in-app notification is sent to an invitee before they join. The inviting Admin sees a success message showing the copyable link and its 7-day expiry timestamp.

---

### 3.11 Settings & Configuration

#### Workspace Settings (Admin only)
- **General**: Workspace name, logo URL.
- **Defaults**: Timezone, date format (MM/DD/YYYY or DD/MM/YYYY), currency.
- **Time Tracking**:
  - Rounding rule (None / nearest / up / down + interval).
  - Mandatory description toggle (requires description on every entry).
  - Max timer duration (default 24h).
  - Past entry limit (how many days back manual entries are allowed; default 7).
- **Compliance**:
  - Rolling lock period in days (default 7).
  - Timesheet Approval workflow toggle (default off).
- **Idle Detection**:
  - Enable/disable idle detection.
  - Idle timeout duration (1, 2, 5, 10, or 15 minutes).
- **Danger Zone**:
  - Delete workspace (confirmation modal required).
  - Revoke pending invite links.

#### User Settings (self-service)
- Profile: display name, profile photo URL.
- Change password (email/password accounts only).
- Weekly hours goal (personal target shown on dashboard).
- Timezone override (overrides workspace default for display purposes only).
- Notification preferences: reserved for post-MVP.

---

### 3.12 Super Admin Dashboard

> **Implementation Status:** Backend (API-only) complete as of Phase 1.5.
> Frontend UI to be built after Phase 2 is completed and approved.
> Full UI specification is in UI/UX Blueprint v2.0 Part 14.

The Super Admin Dashboard is a platform-level internal tool accessible only
to Yusi Time founders and staff (`is_superadmin = TRUE` on the `users` table).
It is completely separate from the standard workspace application and is never
visible to any workspace role (Admin, Manager, Member, or Viewer).

#### Access & Authentication
- Super Admin is identified by `is_superadmin: true` in the `GET /users/me`
  response. This flag is set directly in the database — no UI, no registration
  flow, no promotion by workspace Admins.
- The Super Admin Dashboard is accessible at `/superadmin` in the web
  application, protected by middleware that checks `is_superadmin`.
- A Super Admin may simultaneously hold a workspace role in any workspace.
  Their Super Admin privileges are a parallel track — they do not interfere
  with their workspace role in any workspace they belong to as a regular member.

#### Platform Management Capabilities
- **View all workspaces** across the entire platform without being a workspace
  member. Full workspace detail including settings, member count, and creation date.
- **View all users** across the entire platform. Full user detail including
  workspace memberships and roles.
- **Inspect any workspace** — access any workspace's members, projects, clients,
  tags, and settings as if they were a workspace Admin.
- **Bypass the invite system** — access any workspace endpoint without a
  membership record in `workspace_members`.
- **Platform statistics** — aggregate counts of workspaces, users, time entries,
  and active timers across the entire platform.

#### What Super Admin Cannot Do (MVP Scope)
- Cannot modify `is_superadmin` for any user via the UI — database only.
- Cannot impersonate a specific user's session.
- Cannot view time entry financial data that is hidden from Viewers in a
  workspace where they hold a Viewer role (their workspace role still applies
  when acting within that workspace as a member — Super Admin bypass only
  applies to the platform-level API endpoints).
- Cannot delete user accounts via the Super Admin UI in this pass.
- Cannot access a dedicated audit log of their own Super Admin actions in
  this pass (deferred to future enhancement).

---

## 4. User Permissions & Roles

> **Super Admin note:** Any user with `is_superadmin = true` is a
> **platform-level operator** that exists outside this role table entirely.
> Super Admin bypasses all workspace membership checks and all role-based
> access controls unconditionally. They are never bound by the permissions
> below. See §3.12 and §5 for full Super Admin business rules.

| Action | Admin | Manager | Member | Viewer |
|--------|-------|---------|--------|--------|
| Manage workspace settings | ✅ | ❌ | ❌ | ❌ |
| Invite members to workspace | ✅ | ❌ | ❌ | ❌ |
| Manage roles of existing members | ✅ | ❌ | ❌ | ❌ |
| Remove members from workspace | ✅ | ❌ | ❌ | ❌ |
| Create / edit / delete clients, projects, tasks | ✅ | ✅ | ❌ | ❌ |
| View projects and tasks | All public + all private | All public + all private | Public + assigned private | Public + assigned private |
| Log time on projects | ✅ | ✅ | On visible projects only | ❌ |
| Edit / delete own unlocked entries | ✅ | ✅ | ✅ | ❌ |
| Edit / delete any member's entries | ✅ | ✅ | ❌ | ❌ |
| Override locked entries (unlock) | ✅ | ❌ | ❌ | ❌ |
| Continue entry (start new timer from past entry) | ✅ | ✅ | ✅ (own draft/approved entries only) | ❌ |
| Duplicate entry | ✅ | ✅ | ✅ (own draft/approved entries only) | ❌ |
| Submit weekly timesheet | ✅ | ✅ | ✅ | ❌ |
| Approve / reject timesheets | ✅ | ✅ | ❌ | ❌ |
| View reports | All data + financials | All data + financials | Own data only | Hours + descriptions only |
| View Weekly Report | All members' data | All members' data | Own row only | Own row only |
| Set billable rates | ✅ | ✅ | ❌ | ❌ |
| Generate / revoke invite links | ✅ | ❌ | ❌ | ❌ |

**Viewer financial data restriction**: Viewers never see billable amounts, hourly rates, currency values, or cost totals anywhere in the application — not in project views, time entry lists, reports, dashboards, or API responses scoped to their session.

---

## 5. Business Rules & Validation Logic

### Time Entry Validation
- Start datetime must be before or equal to end datetime.
- Project is mandatory on every time entry.
- Overlapping entries for the same user produce a soft inline warning but are not blocked.
- When the approval workflow is enabled, submitted (Pending) entries cannot be edited or deleted by the Member. They can only be modified after a Manager/Admin rejection.
- Manual entries cannot be backdated beyond the workspace's configured past-entry limit.

### Continue Entry Rules (NEW — v1.3)
- Continue is permitted on `draft` and `approved` entries.
- Continue is **not permitted** on `pending` entries — returns `400 CANNOT_CONTINUE_PENDING`.
- Continue creates a brand-new time entry. The source entry is unchanged.
- A fresh rate snapshot is taken for the new entry at creation time.
- If a timer is already running when Continue is called without `force=true`, returns `409 TIMER_ALREADY_RUNNING`.
- With `force=true`, the running timer is stopped first (with rounding applied), then the Continue timer starts.
- Continue by a Member on another Member's entry: returns `403 FORBIDDEN` unless the caller is Manager or Admin.

### Duplicate Entry Rules (NEW — v1.3)
- Duplicate is permitted on `draft` and `approved` entries.
- Duplicate is **not permitted** on `pending` entries — returns `403 FORBIDDEN`.
- Duplicate creates a brand-new `draft` entry. The source entry is unchanged.
- The duplicated entry's `start_time` is the start of the current calendar day in the workspace timezone. `end_time` = `start_time` + source `duration_seconds`.
- Rounding is applied to the duplicated entry's duration on save (same as any new entry).
- A fresh rate snapshot is taken for the duplicated entry.
- Duplicate by a Member on another Member's entry: returns `403 FORBIDDEN` unless the caller is Manager or Admin.
- Duplicate respects the past-entry limit: the new entry's start_time is today, so this is never an issue.

### Description Draft Auto-Save Rules (NEW — v1.3)
- Stored in `localStorage` under key `yt_desc_draft_{userId}_{workspaceId}`.
- Cleared on successful timer start, timer stop, or manual entry save.
- Cleared when the running timer's description is loaded from the server on page load.
- Never sent to or stored on the server. Purely client-side.

### Weekly Report Rules (NEW — v1.3)
- Date range defaults to the current Mon–Sun week.
- Members and Viewers see only their own row; `user_id` is automatically locked to their own ID server-side.
- Admins and Managers see all members' rows.
- Financial columns (billable amounts, hourly rates) absent for Viewer role.
- The report aggregates all entry statuses (draft, pending, approved) together into the cell total. Status is shown as a breakdown in the cell popover detail.

### Rounding
- Applied server-side on every save (new entry and edit).
- Rounding is computed from the raw duration submitted in that save operation.
- The original raw seconds are not stored.
- The UI must display the rounded result via a non-blocking toast notification after every save.
- Manual entry forms show a rounded preview before the user confirms.

### Rate Snapshot
- At entry creation (or on edit, for the edited entry), the effective rate is fetched from the rate hierarchy and stored on the entry record.
- Subsequent changes to rates at any level do not affect entries that have already been saved.
- Continue and Duplicate both take a fresh rate snapshot at creation time — they do not inherit the source entry's rate.

### Timer Singleton
- Only one active timer per user per workspace at any time.
- `GET /time-entries/current` returns the active timer if one exists.
- Starting a new timer without `force=true` returns HTTP 409 if another timer is already running.
- With `force=true`, the previous timer is stopped and saved (with rounding) before the new one starts.

### Workspace Soft Delete
- A soft-deleted workspace returns HTTP 404 on all API requests.
- Data is retained in the database for 30 days.
- After 30 days, all data is permanently and irreversibly deleted.

### Idle Prompt
- The idle modal must be explicitly dismissed by the user choosing one of the three options.
- No other UI action (outside of the modal) can be taken while the modal is displayed.
- If the user manually stops the timer while in idle state, the modal appears before the entry is finalized.

### Invite Link Rules
- Invite links expire 7 days after generation.
- A link can only be used once (single-use): after a user successfully joins via the link, it is invalidated.
- An Admin can revoke a pending link before it is used or expires.
- Attempting to use an expired or revoked link returns an informative error page prompting the invitee to request a new link.

### Approval Toggle Transition
- Disabling approvals mid-use: Pending entries remain locked to the member. Approved entries fall under the rolling lock date. Unlocked entries fall under the rolling lock date immediately.
- Enabling approvals: Only affects new submissions going forward. Existing date-locked entries are not affected.

### Super Admin Rules

- `is_superadmin = TRUE` is a boolean flag on the `users` table. It is not
  a value in the `workspace_role` enum and never appears in `workspace_members`.
- Super Admin bypasses `get_workspace_member()` via a synthetic member object
  with `role='admin'`. The `workspace_members` table is never queried for them
  on workspace-scoped requests.
- Super Admin bypasses all `require_role()` checks unconditionally. Every
  endpoint in the API is accessible regardless of the role requirement.
- `is_superadmin` is set exclusively via direct database SQL by platform
  engineers. No application endpoint, no workspace Admin UI, and no
  registration flow can set this flag.
- `is_superadmin` is always `FALSE` on newly created users regardless of
  signup method (email/password or Google OAuth). It is not present in any
  request schema.
- The `UserPublic` schema always includes `is_superadmin: bool`. The frontend
  reads this from `GET /users/me` to gate the Super Admin UI route and
  navigation elements.
- Super Admin appearing inside a workspace always presents as `role='admin'`
  for response serialization purposes. They receive full financial data
  visibility with no Viewer data isolation restrictions on any workspace.
- No audit logging specific to Super Admin actions in Phase 1.5. Standard
  service-layer audit log entries are still written for any mutations a Super
  Admin makes through existing service functions.
- The dedicated `get_superadmin_user` FastAPI dependency guards all
  Super Admin-only platform endpoints (`/admin/*`). It raises
  `403 FORBIDDEN` for any user where `is_superadmin is False`.
- Super Admin-only endpoints use the `/admin/` path prefix and are defined
  in `backend/app/routers/admin.py` (created in the Super Admin UI phase).

---

## 6. User Stories (Key Flows)

1. **Invite a team member**: Admin navigates to Members settings, enters an email, selects role "Member", clicks "Generate Invite Link". A link is displayed with a 7-day expiry. Admin copies it and sends via Slack. Invitee clicks the link, creates an account, and is automatically added to the workspace as a Member.

2. **Track and round time**: Freelancer starts a timer, works 1 hour 3 minutes, stops. A toast notification appears: "Timer stopped at 1h 3m. Saved as 1h 15m (rounded up to nearest 15 min)." The freelancer trusts the system and invoices accordingly.

3. **Submit and approve timesheet**: Member clicks "Submit Week". A dialog shows only the unlocked/unapproved entries for that week (already-approved entries from prior cycles are listed separately as excluded). Member confirms. Entries lock immediately. Manager opens the Approvals dashboard, reviews the submitted week, and clicks "Approve". Entries are now permanently locked and marked Approved.

4. **Reject and resubmit**: Manager reviews submitted timesheet and rejects with note: "Missing descriptions on Tuesday entries." Member receives an in-app notification. All submitted entries for that week unlock. Member adds descriptions, resubmits. Manager approves.

5. **Viewer sees only hours**: External client is assigned to a private project by the Admin. Client logs in, navigates to the project, opens the Summary Report. They see total hours by day and task descriptions. All rate, currency, and billable amount fields are absent from their view.

6. **Idle detection — discard and continue**: Developer starts a timer, gets called away for 20 minutes. On return, the timer shows "Idle: 20 min". Developer chooses "Discard Idle Time & Continue". The first entry is saved ending at the moment they went idle. A new timer automatically starts from the moment they clicked the button.

7. **Expired invite link**: Admin generates an invite link. Invitee receives it but doesn't act for 8 days. On clicking the link, they see: "This invite link has expired. Please ask your workspace Admin to generate a new one."

8. **Continue entry (NEW — v1.3)**: Freelancer finishes lunch, opens the Dashboard, sees yesterday's "Client Meeting — Project Alpha" entry. Clicks the Continue (▶) button. A new timer starts immediately with the same project, task, description, and billable flag. The freelancer doesn't have to re-select anything.

9. **Duplicate recurring entry (NEW — v1.3)**: Developer tracks the same daily standup every morning against the same project and task. On Monday, they duplicate Friday's standup entry. A new draft entry is created for today with the same project, task, and description, starting at midnight with the same duration. Developer edits the start/end time and saves.

10. **Description draft saved across refresh (NEW — v1.3)**: Developer types "Implementing OAuth2 flow for—" in the timer bar description, then accidentally closes the tab. On reopening Yusi Time, the description field is pre-filled with "Implementing OAuth2 flow for—". No work is lost.

11. **Manager reviews Weekly Report (NEW — v1.3)**: Agency manager opens `/reports/weekly` for the current week. Sees a grid with all team members as rows and Mon–Sun as columns. At a glance identifies that Sam logged 0 hours on Wednesday and follows up. Clicks Wednesday's cell for Sam — a popover shows Sam had no entries that day. Exports the grid as CSV for payroll processing.

12. **Super Admin inspects a workspace (NEW — v1.4)**: Founder logs in with
    their standard account. The sidebar shows a "Super Admin" link visible
    only to them. They navigate to `/superadmin/workspaces`, see a list of
    all workspaces on the platform with member counts and creation dates.
    They click into "Acme Agency" workspace, see all members, projects, and
    settings without ever having been invited. They identify a misconfigured
    rounding setting and navigate to the workspace settings page within the
    Super Admin dashboard to review it.

13. **Super Admin views platform statistics (NEW — v1.4)**: Founder opens
    `/superadmin` dashboard home. They see platform-wide aggregate stats:
    total workspaces (47), total users (312), total time entries logged
    (18,429), currently active timers (7). They use this to monitor platform
    health without needing access to any individual workspace's private data.

---

## 7. Design & UX Requirements (High-Level)

- **Consistent component states**: Every data-driven component must implement: Loading (skeleton), Empty (illustration + call-to-action), Error, and Disabled states.
- **Rounding feedback**: Non-blocking toast notification shown after every timer stop or manual entry save, displaying the rounded result explicitly.
- **Idle prompt**: Modal dialog with three clearly labeled buttons. No auto-dismiss. No background interaction while modal is open.
- **Invite flow**: Invite dialog shows an email input and role selector. After submission, displays the generated link in a read-only text field with a "Copy Link" button, an expiry notice ("Expires in 7 days — [date]"), and a "Done" button.
- **Approvals dashboard**: "Submit Week" button is disabled if no unlocked/unapproved entries exist in the selected week. Submitted weeks display a "Pending" badge on each cell. Approved weeks display an "Approved" badge.
- **Viewer UI**: Financial columns, rate fields, and currency displays are completely absent from the DOM for Viewer sessions — not hidden via CSS, but not rendered at all.
- **Rounding preview**: In the manual entry form, a live preview of the rounded duration appears below the duration input as the user types, before saving.
- **Continue button UX (NEW — v1.3)**: The Continue (▶) button appears on every draft/approved entry row. It must be clearly visually differentiated from Edit. It must be absent (not disabled) on pending entries. Clicking Continue while a timer is already running triggers a confirmation prompt before stopping the current timer.
- **Duplicate UX (NEW — v1.3)**: Duplicate lives in the three-dot context menu of each entry row alongside Edit and Delete. It must be absent on pending entries. On successful duplicate, the rounding toast appears with the new entry's rounded duration.
- **Weekly Report UX (NEW — v1.3)**: The weekly grid is scannable at a glance. Zero-hour cells are visually de-emphasized (muted). Cells with hours are clearly prominent. Clicking any cell shows a lightweight popover with individual entry details for that user+day. The report respects the same role-based data isolation as all other reports.

*(Detailed screen-by-screen UI/UX Blueprint is maintained as a separate document.)*

---

## 8. Assumptions & Constraints

- MVP runs on a single-instance PostgreSQL database. Workspace isolation is enforced at the application layer via `workspace_id` on all queries.
- AWS deployment stack: Amplify (web frontend), ECS (backend API), RDS PostgreSQL (database), SES (password reset email only).
- Expected max concurrent users: ~100. No Redis cache or message queue in MVP.
- Idle detection depends on browser-level activity events (mousemove, keydown, touchstart). It is not foolproof and does not work when the browser tab is in the background on some browsers.
- Description draft auto-save uses `localStorage` and is therefore per-browser, per-device. Clearing browser data removes drafts.
- English-only UI. No internationalization (i18n) framework in MVP.
- Password minimum: 8 characters. No complexity enforcement.
- No mobile app in MVP. The web application is responsive for basic use on mobile browsers, but the native Flutter app is post-MVP.

---

## 9. Out of Scope for MVP

- Full invoicing engine (PDF generation, invoice sending)
- GPS tracking, screenshots, activity monitoring
- Kiosk mode, Pomodoro timer
- Native integrations with Jira, Asana, Slack, etc.
- Multi-currency support within a single workspace
- SSO / SAML authentication
- Mobile offline support (native app is post-MVP)
- AI-powered time suggestions or anomaly detection
- Individual entry-level rejection in approval workflow (full-week rejection only in MVP)
- Manager invite permissions (Managers cannot invite; Admin-only)
- Super Admin audit logging (dedicated audit trail for Super Admin actions — post-MVP)
- Super Admin user impersonation (acting as a specific user's session — post-MVP)
- Super Admin `is_superadmin` flag management via UI (database-only in all MVP phases)
- Super Admin account deletion of workspace users via dashboard (post-MVP)
- Configurable invite link expiry (fixed at 7 days in MVP)
- Notification preferences per user (reserved for post-MVP)
- Timesheet week templates / copy-last-week (post-MVP)
- Bulk edit of multiple time entries simultaneously (post-MVP)
- Shareable live report links (post-MVP)
- Scheduled email delivery of reports (post-MVP)
- Calendar drag-to-block time entry view (post-MVP)

---

## 10. Acceptance Criteria Overview

| Feature | Acceptance Criteria |
|---------|-------------------|
| Invite link generation | Admin generates link; link expires after exactly 7 days; single-use; revocable; expired/used links show error page |
| Invite permissions | Only Admins can generate invite links; Manager invite UI does not exist |
| Time rounding | Toast appears after every save showing rounded result; manual entry form shows live preview; rounding applies on edit as well as new entry |
| Timesheet submission | Submit Week dialog shows only unlocked/unapproved entries; already-approved entries in same week are excluded; entries lock immediately on confirm |
| Approval workflow | Approve locks entries as Approved; Reject unlocks entries with mandatory note; Member notified of both outcomes |
| Approval toggle transition | Disabling approvals: Pending entries stay locked; Approved entries fall under lock date; unlocked entries follow lock date immediately |
| Viewer data restriction | Viewers see no financial data anywhere in UI or API responses; financial fields are not rendered, not merely hidden |
| Idle detection | All three options functional; no auto-dismiss; timer state correct after each choice; cross-device independence confirmed |
| Invite link single-use | Link invalidated immediately after successful join; second use returns error |
| Continue entry (NEW) | Continue starts new timer with same project/task/description/billable/tags; fresh rate snapshot taken; pending entries return 400 CANNOT_CONTINUE_PENDING; timer conflict handled via force flag |
| Duplicate entry (NEW) | Duplicate creates draft entry with same metadata; start_time = today midnight; rounding applied; pending entries return 403; rounding toast shown |
| Description draft auto-save (NEW) | Draft persists across page refresh; draft cleared on successful timer start/stop; draft not sent to server; draft scoped per user per workspace |
| Weekly Report (NEW) | Grid shows all members × days for selected range (Admin/Manager); Members/Viewers see own row only; cell popover shows individual entries; CSV export available; financial data absent for Viewers |
| Super Admin backend (Phase 1.5) | `is_superadmin=TRUE` user accesses any workspace endpoint without membership — 200 success; `is_superadmin=FALSE` user calling `/admin/*` endpoint — 403 FORBIDDEN; newly registered user always has `is_superadmin=FALSE`; `require_role('admin')` called with Super Admin user — bypassed unconditionally |
| Super Admin UI (post-Phase 2) | `/superadmin` route inaccessible to non-super-admin users; platform workspace list shows all workspaces; platform user list shows all users; platform stats widget shows correct aggregate counts; Super Admin nav link absent from DOM for all non-super-admin sessions |

---

## 11. Glossary

| Term | Definition |
|------|-----------|
| Workspace | A tenant container holding all projects, members, settings, and time data. Users can belong to multiple workspaces. |
| Time Entry | A single logged block of work with a start time, end time (or duration), project, and optional metadata. |
| Timesheet | The collection of a user's time entries for a given calendar week (Monday–Sunday). |
| Submit | The act of a Member locking their week's unapproved entries and sending them for managerial review. |
| Pending | Timesheet status after submission; entries are locked to the member, awaiting approval or rejection. |
| Approved | Final status after a Manager/Admin approves a submitted timesheet. Entries are permanently locked. |
| Unlocked / Editable | An entry that has not been submitted, or has been rejected and reverted. The member can edit or delete it. |
| Rolling Lock Date | A workspace-configured number of days. Entries older than (today − lock_days) are read-only for non-Admins. |
| Idle Detection | A per-device, per-browser feature that monitors user inactivity and surfaces a prompt when the configured timeout is reached during an active timer. |
| Rate Snapshot | The effective hourly rate stored on a time entry at the moment of creation. Immune to subsequent rate changes. |
| Invite Link | A single-use, time-limited URL generated by an Admin that allows a specific invitee to join a workspace with a pre-assigned role. |
| Billable Amount | The monetary value of a time entry, computed as rounded duration (hours) × snapshotted hourly rate. Never visible to Viewers. |
| Continue | Starting a new timer pre-filled with the project, task, description, billable flag, and tags of a previously completed entry. |
| Duplicate | Creating a new draft time entry with the same metadata as an existing entry, dated to today. |
| Description Draft | A locally-stored (localStorage) in-progress description text that persists across page refreshes. Never sent to the server. |
| Weekly Report | A report showing hours logged per user per day in a grid format, covering a selected date range. |
