# Yusi Time — Documentation Addendum v1.0
## Scheduled Attendance, Daily Hour Targets, Workspace Billable Toggle, Enhanced Idle Detection

**Date:** 2026-06-21 (Revision 2 — adds Flexible Hours attendance mode)
**Status:** Approved scope addition to MVP (confirmed by human supervisor — not post-MVP)
**Supersedes:** Nothing. This is an ADDITIVE delta to PRD v1.4, DB Schema v2.2, API Spec v1.1, TRD v1.3, UI/UX Blueprint v2.0.
**Applies starting:** Phase 6.5 (insert before Phase 7 — Reports & Analytics)

This document is the single source of truth for four new features approved by
the human supervisor on 2026-06-21. It is written in the same authority
structure as the base documents: anything not stated here falls back to the
base documents unchanged. Where this addendum is silent, the base documents
govern. Where this addendum specifies something new, it governs.

---

## TABLE OF CONTENTS

1. Feature Summary
2. PRD Addendum — New User Stories & Business Rules
3. Database Schema Addendum — New Tables & Columns
4. API Spec Addendum — New Endpoints
5. TRD Addendum — New Architecture Component (Scheduler)
6. UI/UX Blueprint Addendum — New Screens & Component States
7. Out-of-Scope Items (Explicitly Logged)
8. Open Risk Notes

---

## 1. FEATURE SUMMARY

| ID | Feature | One-Line Description |
|----|---------|----------------------|
| F1 | Scheduled Work-Start Prompt | Admin sets a fixed daily clock time and an attendance mode (Fixed Schedule or Flexible Hours); Members get a blocking modal at that time — either a "start now" prompt (Fixed mode) or a "still time to log hours" reminder (Flexible mode), with late-arrival detection in Fixed mode |
| F2 | Daily Required Hours | Admin sets a global daily hour target; live progress indicator, soft-block warnings on early stop/logout/tab-close, end-of-day manager/admin notification on shortfall |
| F3 | Workspace Billable Toggle | Admin can mark the whole workspace non-billable, suppressing all rate/billable computation workspace-wide without deleting stored rate data |
| F4 | Enhanced Idle Detection (Web) | Adds the native browser `IdleDetector` API (Chrome/Edge only) as an enhancement layer on top of the existing browser-activity-based idle detection, which remains the fallback for Firefox/Safari |

**Explicitly out of scope (logged to backlog, not built now):**
- True OS-level idle detection independent of the browser (Desktop App phase only)
- Desktop app auto-start on boot (Desktop App phase only)
- Per-member daily hour targets (workspace has ONE global number only)
- Per-member attendance mode (workspace has ONE mode — Fixed Schedule OR
  Flexible Hours — applied to all Members; mixing modes within a workspace
  is not supported)
- Manager-to-member direct-report assignment model (Manager role remains workspace-wide)

---

## 2. PRD ADDENDUM — NEW USER STORIES & BUSINESS RULES

### 2.1 New Workspace Settings Fields

The Workspace Settings screen gains a new section: **"Attendance & Schedule"**,
positioned below the existing workspace settings sections (per Blueprint
Addendum §6 for exact placement).

New fields, all Admin-only to view and edit:

| Field | Type | Default | Description |
|-------|------|---------|--------------|
| `attendance_enabled` | boolean | `false` | Master toggle for F1 + F2. When OFF, no triggers fire, no notifications sent, no indicators shown. |
| `attendance_mode` | enum: `'fixed_schedule'` \| `'flexible_hours'` | `'fixed_schedule'` | Workspace-wide mode. ONE mode applies to ALL Members in the workspace — mixing modes within a workspace is not supported (confirmed 2026-06-21). Determines how `work_start_time` is interpreted (see PRD-ADD-02b). |
| `work_start_time` | time (HH:MM, no seconds) | `null` | **Fixed Schedule mode:** the exact clock time the work-start prompt fires, with late-arrival detection if a Member's first action that day is after this time. **Flexible Hours mode:** the clock time at which a one-time "gentle reminder" check fires — there is no late-arrival concept in this mode, since there is no expected start time to be late against. |
| `daily_required_hours` | decimal(4,2) | `null` | Global daily hour target in hours (e.g. `5.00`). Applies to all Members, in both attendance modes. |
| `off_days` | array of integers (0=Sunday...6=Saturday) | `[0]` (Sunday) | Days of the week on which F1 and F2 are both suspended entirely. Admin-configurable via checkboxes. |

**Business rule PRD-ADD-01:** `attendance_enabled` is the master switch. If
`false`, `work_start_time` and `daily_required_hours` may still be stored
(Admin can configure them in advance) but no scheduler job evaluates them and
no UI elements render. This mirrors the existing pattern for the approval
workflow toggle (PRD §3.6, Toggle OFF semantics).

**Business rule PRD-ADD-02:** If `attendance_enabled = true` but either
`work_start_time` or `daily_required_hours` is `null`, that specific
sub-feature (F1 or F2) is treated as disabled while the other (if configured)
remains active. Both fields are independently nullable — an Admin can enable
only the work-start prompt without a daily hour target, or vice versa.

**Business rule PRD-ADD-02b:** `attendance_mode` determines which F1 variant
fires at `work_start_time` — Fixed Schedule mode (the original work-start
prompt with late-arrival detection) or Flexible Hours mode (a single daily
"gentle reminder" with no concept of lateness). Both variants reuse the same
underlying blocking modal component and the same `work_start_time` field —
only the copy, the absence/presence of a late-arrival calculation, and the
suppression condition (see PRD-ADD-08 below) differ. This is a single
workspace-wide setting; a workspace cannot have some Members on Fixed
Schedule and others on Flexible Hours.

**Business rule PRD-ADD-03:** F1 and F2 apply **only to the Member role**.
Admin and Manager roles are fully exempt — no prompts, no warnings, no
inclusion in missed-hours checks, regardless of `attendance_enabled` state.

**Business rule PRD-ADD-04:** Both F1 and F2 are suspended entirely on any
day-of-week listed in `off_days`. "Suspended" means: the work-start scheduler
job does not evaluate that workspace on that day, and the daily-hours
shortfall check does not run for that day. Time logged voluntarily on an
off-day is tracked completely normally — only the prompts/warnings/checks
are suspended, not time tracking itself.

### 2.2 Feature F1 — Scheduled Work-Start Prompt (Two Modes)

**User Story (Member, Fixed Schedule mode):** As a Member on a fixed
schedule, when the workspace's configured work start time arrives and I have
not yet started a timer that day, I see a blocking modal asking if I want to
start tracking now, so the system can help me remember to log my time.

**User Story (Member, Flexible Hours mode):** As a Member with flexible
hours (e.g. a part-time contract requiring N hours/day with no fixed start
time), I want a single gentle reminder later in the day if I haven't logged
any time yet, without being treated as "late" — because I have no fixed
start time to be late against.

**User Story (Admin):** As an Admin, I want to choose whether my workspace
operates on a fixed daily start time or flexible hours, and configure the
relevant trigger time and daily hour target accordingly, so the system
matches how my team actually works.

**Trigger logic — Fixed Schedule mode (`attendance_mode = 'fixed_schedule'`):**
- Evaluated per-Member, using that Member's stored timezone (see §3.4 for
  the unresolved exact field-name dependency).
- Fires once at `work_start_time` if and only if: `attendance_enabled = true`,
  `work_start_time` is set, today is not in `off_days`, and the Member has
  no time entry (of any status) with a `start_time` today.
- **Late arrival case:** If the Member's first action of the day (login, or
  manually opening the app) occurs after `work_start_time` has already
  passed, the SAME blocking modal appears immediately, but with a variant
  message stating how late they are (e.g. "You are 47 minutes late — start
  tracking now?"). This is the same component with a computed `lateBy`
  duration, not a separate flow.

**Trigger logic — Flexible Hours mode (`attendance_mode = 'flexible_hours'`):**
- `work_start_time` is repurposed as the single daily check-in time (e.g.
  Admin sets it to `18:00` to mean "check at 6 PM"), NOT a required start
  time. There is no "late" concept in this mode.
- Fires once at `work_start_time` if and only if: `attendance_enabled = true`,
  `work_start_time` is set, today is not in `off_days`, AND the Member has
  logged **zero** time entries so far that calendar day (any status, any
  project). Per human supervisor decision 2026-06-21, the reminder uses the
  same blocking modal as Fixed mode, with reworded copy: "Still time to log
  hours today — start tracking?" — no late-arrival language, no lateness
  calculation performed.
- **Suppression condition (PRD-ADD-08):** If the Member has already logged
  ANY time that day before `work_start_time` arrives — even a small amount,
  not yet meeting `daily_required_hours` — the reminder does NOT fire at
  all. It only fires for Members at exactly zero hours logged so far. This
  reflects that a flexible-hours Member who already started working has no
  need for a "let's start" prompt; their progress toward the target is
  already covered by the Timer Bar daily progress badge (§6.4) and the
  midnight shortfall check (§2.3), not by this reminder.

**No re-prompt (both modes):** If the Member dismisses or ignores the
prompt (selects "No"/"Not Now" or the prompt times out per UI spec), it is
NOT re-shown later that day in either mode. An unread in-app notification
record is created so the event is not silently lost, but no further
interruption occurs.

**Modal interaction (per human supervisor decision 2026-06-21):**
- Blocking modal, same interaction pattern as the existing Idle Modal
  (TRD/Blueprint §3.5 / FRONTEND_SKILL.md §3.5): no X button, no backdrop
  dismiss, no Escape key dismiss. Identical shell for both attendance
  modes — only copy and the presence/absence of a `lateBy` value differ.
- Two choices only: **"Start Tracking"** (opens project/task selector inline
  in the same modal, then starts the timer on confirm) and **"Not Now"**
  (dismisses, creates the unread notification record, does not re-prompt).

**Delivery:**
- In-app blocking modal (primary).
- Browser push notification (secondary channel) — fires simultaneously so
  Members with the tab backgrounded or closed still get notified. Clicking
  the push notification focuses/opens the app to the same blocking modal
  state. See §5 for push infrastructure.

### 2.3 Feature F2 — Daily Required Hours

**Mode-agnostic note:** Everything in this section applies identically
regardless of `attendance_mode` (Fixed Schedule or Flexible Hours) — F2 is
purely deadline-based (did the Member reach `daily_required_hours` by
midnight?), with no dependency on when in the day the hours were logged.
This is the feature that actually solves the "part-time, work whenever,
just hit 5h/day" scenario — confirmed 2026-06-21.

**User Story (Member):** As a Member, I want to see how many hours I've
logged today against the workspace's daily target, so I know if I'm on
track before I try to stop working.

**User Story (Admin/Manager):** As an Admin or Manager, I want to be
notified if a Member logs fewer than the required hours on a given day, so
I can follow up with them.

**Live indicator:**
- Persistent badge in the Timer Bar (visible to Members only, only when
  `attendance_enabled = true` and `daily_required_hours` is set), showing
  current cumulative tracked time today vs target (e.g. `"3.2h / 5h"`).
- Indicator switches to a warning visual state (per Blueprint Addendum §6.3
  for exact styling) when remaining time-in-day makes hitting the target
  increasingly unlikely. Exact pacing threshold left to UI/UX Blueprint
  Addendum for a concrete formula — flagged in §8 Open Risk Notes.

**Soft-block warning triggers (all three, per human supervisor decision):**
1. Member clicks "Stop Timer" while a timer is running AND cumulative hours
   today (including the entry about to be stopped) is below
   `daily_required_hours`.
2. Member clicks "Log Out" while cumulative hours today is below target.
3. Member attempts to close the browser tab/window while cumulative hours
   today is below target AND a timer is currently running (browser
   `beforeunload` prompt — note browser-native limitation in §8).

**Warning behavior:** Non-blocking confirmation (shadcn AlertDialog pattern,
consistent with RULE F-09 / forbidden `window.confirm()`): "You've logged
X.Xh of Yh today. Stop anyway?" with Cancel / Confirm. This is NOT a hard
block — the action proceeds if the Member confirms. Case 3 (tab close) is
constrained by browser `beforeunload` API limitations — see §8.

**End-of-day shortfall check:**
- Runs once per workspace at midnight in that workspace's configured
  timezone (existing field — confirm exact name against live schema in
  Phase 6.5 Step 1).
- For each Member, sums `duration_seconds` across ALL time entries (any
  project, any task, any status) with a date matching that calendar day.
- If the sum is less than `daily_required_hours × 3600` seconds, AND that
  day is not in `off_days`, a notification is created and sent to **every**
  Admin and **every** Manager in the workspace (no direct-report model
  exists — confirmed 2026-06-21).
- This check does NOT apply to Admin or Manager roles' own time (PRD-ADD-03).

### 2.4 Feature F3 — Workspace Billable Toggle

**User Story (Admin):** As an Admin, I want to mark my entire workspace as
non-billable, so that none of my projects or tasks can have billable rates,
which matches how my organization actually operates (e.g. internal teams,
nonprofits, agencies tracking hours without invoicing).

**New field:** `workspaces.is_billable` (boolean, default `true` — existing
workspaces remain billable by default on migration, since this preserves
all current documented behavior unchanged for every existing workspace).

**Business rule PRD-ADD-05:** When `is_billable = false`:
- No project, task, or client under that workspace can have a non-null
  `hourly_rate_cents` applied in any NEW rate computation. The rate
  hierarchy resolution (TRD §6.6 / Rate Snapshot Rules) short-circuits to
  `null` for the entire workspace regardless of what is configured at the
  task/project/client/workspace-default level.
- Existing stored `hourly_rate_cents` values on tasks/projects/clients/
  workspace default are **NOT deleted or modified**. They remain in the
  database exactly as they were (per human supervisor decision 2026-06-21).
- Existing time entries that already have a `billable_amount_cents` snapshot
  retain that value unchanged (Rate Snapshot Rules: "once saved, rate never
  changes on an existing entry" — this is consistent with, not a new
  exception to, existing TRD behavior).
- The Billable toggle/column on Project and Task forms **remains visible**
  but displays "Not billable" / disabled state (per human supervisor
  decision 2026-06-21) — this is a deliberate deviation from the
  absent-not-hidden pattern used for Viewer role, because the data is not
  being hidden from an unauthorized role; it is being suppressed by a
  workspace-level configuration that any Admin can see and reason about.
- All Reports (Phase 7 scope) that show billable totals/financials must
  read `workspace.is_billable` and suppress those columns/totals
  entirely when `false` — this is a forward-looking note for Phase 7 and
  must be incorporated into that phase's checklist, not built now.

**Business rule PRD-ADD-06:** Toggling `is_billable` back to `true` restores
full rate computation immediately using whatever rate hierarchy values are
currently stored — no data re-entry required, since nothing was deleted.

### 2.5 Feature F4 — Enhanced Idle Detection (Web)

**User Story (Member):** As a Member using Chrome or Edge, I want the system
to detect when my whole computer is idle (not just this browser tab), so the
Idle Modal triggers more accurately than tab-only activity tracking.

**Business rule PRD-ADD-07:** This is an **enhancement layer**, not a
replacement. The existing documented idle detection behavior (TRD/Blueprint,
browser-activity/tab-based) remains the baseline and the fallback.

- On browsers where `window.IdleDetector` exists (Chrome 94+, Edge 94+ per
  current support — re-verify against MDN/caniuse at implementation time,
  since browser support can change): request permission via user gesture
  (cannot be requested silently on page load), then use the native idle/
  locked signal as the trigger source for the existing Idle Modal.
- On all other browsers (Firefox, Safari, and Chrome/Edge users who deny
  the permission prompt): fall back to the exact existing behavior
  documented in TRD/Blueprint — no functional regression for those users.
- The Idle Modal itself, its three options (keep & continue / discard &
  stop / discard & continue), and its non-dismissible behavior are
  **completely unchanged** by this feature. Only the *detection signal
  source* changes.
- Permission for `IdleDetector` must be requested separately from (not
  bundled with) the browser push notification permission for F1 — they are
  unrelated browser permissions and bundling the prompts would confuse
  users about what they're granting.

**Honest limitation note (must be visible to Admin in Workspace Settings, not
hidden):** A small info note near any idle-detection-related setting stating
that OS-level idle detection is currently available on Chrome/Edge only, and
that full cross-application OS-level detection requires the upcoming desktop
app.

---

## 3. DATABASE SCHEMA ADDENDUM

All new columns/tables below are additive. No existing column is renamed,
retyped, or dropped. All new boolean/nullable columns default to values that
preserve current behavior for existing workspaces unchanged.

### 3.1 `workspaces` table — new columns

```sql
ALTER TABLE workspaces
  ADD COLUMN attendance_enabled BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN attendance_mode VARCHAR(20) NOT NULL DEFAULT 'fixed_schedule'
    CHECK (attendance_mode IN ('fixed_schedule', 'flexible_hours')),
  ADD COLUMN work_start_time TIME NULL,
  ADD COLUMN daily_required_hours NUMERIC(4,2) NULL
    CHECK (daily_required_hours IS NULL OR daily_required_hours > 0),
  ADD COLUMN off_days INTEGER[] NOT NULL DEFAULT ARRAY[0],
    -- 0=Sunday, 1=Monday, ... 6=Saturday (ISO-adjacent, 0-indexed from Sunday)
  ADD COLUMN is_billable BOOLEAN NOT NULL DEFAULT true;
```

**Note on `attendance_mode`:** stored as `VARCHAR` with a `CHECK` constraint
rather than a native Postgres `ENUM` type, consistent with how other status
fields in the existing schema are implemented (matching the established
pattern — confirm against live schema at implementation time; if the
existing schema uses native enums elsewhere, follow that convention instead
for consistency).

**Migration note (Alembic):** This follows the same hand-written-migration
pattern established in Phase 1.5 (Architecture Decisions Log, 2026-05-31) —
write explicit `upgrade()`/`downgrade()` rather than relying on autogenerate,
since this is a multi-table addition touching a table with existing rows.
`downgrade()` must drop all five columns cleanly.

### 3.2 New table — `attendance_notifications`

Tracks F1 "no response" records and F2 end-of-day shortfall notifications,
separate from the existing general `notifications` table ONLY IF the
existing notification system (built in Phase 6) cannot represent these two
new notification types within its current schema. **This is an open
question for Phase 6.5 Step 1 — see §8.** Proposed structure if a dedicated
table is needed:

```sql
CREATE TABLE attendance_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  notification_type VARCHAR(32) NOT NULL
    CHECK (notification_type IN (
      'work_start_missed',        -- Fixed Schedule mode: no response to prompt
      'flexible_reminder_missed', -- Flexible Hours mode: no response to gentle reminder
      'daily_hours_shortfall'
    )),
  recipient_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- for work_start_missed / flexible_reminder_missed: recipient = user_id (self)
    -- for daily_hours_shortfall: recipient = each Admin/Manager in workspace
  related_date DATE NOT NULL,
    -- the calendar day this notification concerns, in workspace timezone
  late_by_minutes INTEGER NULL,
    -- only set for work_start_missed when the trigger was a late arrival
  hours_logged NUMERIC(5,2) NULL,
    -- only set for daily_hours_shortfall — actual hours logged that day
  is_read BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attendance_notif_recipient
  ON attendance_notifications (recipient_user_id, is_read);
CREATE INDEX idx_attendance_notif_workspace_date
  ON attendance_notifications (workspace_id, related_date);
```

### 3.3 New table — `push_subscriptions`

Required for F1 browser push delivery (Web Push protocol).

```sql
CREATE TABLE push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL,
  p256dh_key TEXT NOT NULL,
  auth_key TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, endpoint)
);
```

**Note:** A user may have multiple subscriptions (multiple browser
profiles/devices). All active subscriptions for a user receive the push.

### 3.4 Confirm-before-build dependency

Per TRD §X (workspace timezone field — exact name to be confirmed against
the live `workspaces` table before Phase 6.5 Step 1 begins). This addendum
assumes a timezone field already exists on `workspaces` per the human
supervisor's confirmation on 2026-06-21 ("each workspace member has a
timezone"). **The build agent must verify the exact column name
(`workspaces.timezone` vs `users.timezone` vs both) against the live schema
before writing any scheduler logic**, since this addendum's business rules
reference "the Member's timezone" and "the workspace's timezone"
interchangeably based on an unverified recollection. See §8.

---

## 4. API SPEC ADDENDUM — NEW ENDPOINTS

All endpoints follow existing conventions: OAuth2/JWT auth, Pydantic V2
request/response models, Router → Service → Model layering, RULE U-01
financial isolation for Viewer (not applicable to these endpoints, but
RULE U-01 governs if any response surfaces rate/billable data).

### 4.1 Workspace Settings

```
PATCH /workspaces/{workspace_id}/attendance-settings
  Auth: Admin only (403 for all other roles)
  Body: {
    attendance_enabled: bool,
    attendance_mode: "fixed_schedule" | "flexible_hours",
    work_start_time: string | null,      # "HH:MM" 24-hour
    daily_required_hours: number | null,  # e.g. 5.00
    off_days: number[]                    # e.g. [0] for Sunday only
  }
  Response: WorkspaceAttendanceSettings (200)
  Errors: 422 if daily_required_hours <= 0; 422 if off_days contains values
          outside 0-6; 422 if work_start_time is not valid HH:MM; 422 if
          attendance_mode is not one of the two allowed values

PATCH /workspaces/{workspace_id}/billable-settings
  Auth: Admin only (403 for all other roles)
  Body: { is_billable: bool }
  Response: WorkspaceBillableSettings (200)
```

### 4.2 Attendance Actions

```
POST /time-entries/work-start-response
  Auth: any authenticated Member
  Body: {
    response: "start" | "not_now",
    project_id: UUID | null,   # required if response == "start"
    task_id: UUID | null
  }
  Response: 200 with created TimeEntry if "start", or 200 ack if "not_now"
  Business rule: creates attendance_notifications(work_start_missed) record
                 if response == "not_now"; computes late_by_minutes server-side
                 by comparing now() to today's work_start_time in workspace tz

GET /time-entries/daily-progress
  Auth: any authenticated Member
  Response: {
    hours_logged_today: number,
    daily_required_hours: number | null,
    on_pace: boolean   # server-computed pacing flag — see §8 for formula
  }
  Business rule: returns daily_required_hours: null and on_pace: true if
                 attendance_enabled is false or daily_required_hours is null,
                 so the frontend can cleanly render no indicator at all
```

### 4.3 Push Notification Subscription

```
POST /users/me/push-subscriptions
  Auth: any authenticated user
  Body: { endpoint: string, p256dh_key: string, auth_key: string }
  Response: 201 PushSubscription

DELETE /users/me/push-subscriptions/{subscription_id}
  Auth: any authenticated user (own subscriptions only — 403 otherwise)
  Response: 204
```

### 4.4 Attendance Notifications (extends existing notification system OR
new dedicated list endpoint — depends on §3.2 resolution)

```
GET /notifications/attendance?recipient_scope=self|managed
  Auth: any authenticated user
  Response: paginated list of attendance_notifications relevant to caller
  Business rule: recipient_scope=managed only returns results for
                 Admin/Manager roles (403 for Member/Viewer requesting
                 managed scope)
```

### 4.5 Response Schema Notes

- `WorkspaceAttendanceSettings` and `WorkspaceBillableSettings` follow the
  existing pattern of dedicated response schemas with
  `model_config = ConfigDict(from_attributes=True)` (RULE B-04).
- `daily-progress` response intentionally flattens to avoid exposing the
  raw `daily_required_hours` field when it's irrelevant — frontend checks
  `daily_required_hours !== null` to decide whether to render the Timer Bar
  badge at all, consistent with RULE F-04 (early-return / conditional
  render patterns).

---

## 5. TRD ADDENDUM — NEW ARCHITECTURE COMPONENT: SCHEDULER

### 5.1 Problem Statement

The existing stack (FastAPI + PostgreSQL, per TRD §5) has no
background/scheduled job runner. Three new behaviors require time-based
triggers independent of any HTTP request:

1. Work-start prompt evaluation at each workspace's configured time, daily.
2. End-of-day shortfall check at each workspace's midnight, daily.
3. (Push notification delivery is request-triggered, not scheduled — no
   new infra needed there beyond the Web Push library itself.)

### 5.2 Recommended Solution: APScheduler (in-process)

**Decision:** Use `APScheduler` (Advanced Python Scheduler) running inside
the existing FastAPI application process, NOT a separate Celery+Redis
deployment.

**Rationale:**
- Avoids introducing Redis or a separate worker deployment for MVP-scale
  job volume (one job per workspace per day, twice — not high throughput).
- Runs in the same async event loop as FastAPI (APScheduler has native
  `AsyncIOScheduler` support compatible with the existing SQLAlchemy async
  session pattern).
- Zero new infrastructure cost on AWS ECS Fargate (TRD §5 Infrastructure) —
  no new container, no new managed service.
- Trade-off acknowledged: APScheduler jobs only run while the FastAPI
  process is alive; if ECS Fargate restarts the container near a trigger
  time, that specific trigger could be missed for that cycle. This is an
  accepted MVP-level trade-off — flagged in §8, not a blocker.

**New dependency:**
```
APScheduler==3.10.4
```

**Job design:**
- A single recurring job (`check_workspace_attendance`) runs every 1 minute,
  queries all workspaces where `attendance_enabled = true`, and for each,
  checks whether `now()` in that workspace's timezone matches
  `work_start_time` (within the 1-minute granularity window) and today is
  not in `off_days`. This avoids needing N separate per-workspace cron
  schedules, which would be unwieldy to manage dynamically as Admins change
  `work_start_time`.
- A second recurring job (`check_daily_shortfall`) runs every 1 minute,
  checks whether `now()` in each workspace's timezone has just crossed
  midnight, and if so runs the shortfall calculation for the previous day.
- Both jobs live in `backend/app/services/scheduler_service.py` (new file,
  follows existing service-layer conventions — stateless functions, called
  from a scheduler bootstrap in `main.py`, not from any router).
- Job logic itself calls existing/new service functions
  (`attendance_service.py` — new file) rather than embedding business logic
  directly in the scheduled callback, consistent with RULE B-06 layering.

### 5.3 Web Push Infrastructure

**New dependency:**
```
pywebpush==2.0.0
```

**Required new config (Settings class, RULE B-07 — env vars, no hardcoding):**
```
VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY
VAPID_CLAIMS_SUBJECT  # mailto: address for push service identification
```

**Frontend requirement:** A Service Worker file
(`web/public/sw.js` or `web/src/app/sw.ts` depending on Next.js PWA tooling
chosen at implementation time) registered on app load, handling
`push` events to display the OS-level notification and `notificationclick`
to focus/open the app to the correct route.

**Permission flow:** Requested via explicit user gesture (e.g. a toggle in
Notification Settings, NOT auto-requested on page load — browsers
increasingly block or auto-deny permission prompts not triggered by user
gesture, and an unsolicited permission prompt is poor UX regardless).

### 5.4 IdleDetector Integration (F4)

No backend changes required — this is frontend-only. New file
`web/src/features/time-tracking/hooks/useEnhancedIdleDetection.ts` (or
equivalent per existing feature-folder convention) wraps the existing idle
detection hook, feature-detecting `window.IdleDetector` and layering the
native signal on top of the existing implementation without replacing it.

---

## 6. UI/UX BLUEPRINT ADDENDUM

This section identifies which existing screens need new component states
and which new screens/modals are required. Full pixel-level specs (exact
spacing, exact copy) are left for the build agent to produce consistent
with existing design tokens (FRONTEND_SKILL.md) — this addendum specifies
WHAT must exist, not the final visual spec, consistent with how this
addendum approaches all sections.

### 6.1 New Modal — Work Start Prompt (Two Variants, One Component)

- Pattern: identical interaction shell to existing Idle Modal (shadcn
  Dialog, `[&>button]:hidden`, `onPointerDownOutside`/`onEscapeKeyDown`
  both prevented).
- **Fixed Schedule mode** — two states: on-time ("Time to start working —
  shall we begin tracking?") and late ("You are {X} late — shall we start
  tracking?").
- **Flexible Hours mode** — one state only, no lateness language: ("Still
  time to log hours today — start tracking?"). Only fires if zero hours
  logged so far that day (PRD-ADD-08) — never shows a "late" variant in
  this mode, since there is no expected start time.
- "Start Tracking" reveals an inline project/task selector (reuse existing
  selector component from Manual Entry Modal, Phase 4) before confirming.
- "Not Now" dismisses immediately, no further confirmation needed.

### 6.2 Workspace Settings — New "Attendance & Schedule" Section

- New settings card following the existing Workspace Settings page layout
  pattern (Phase 2/3 settings pages).
- Fields: toggle (`attendance_enabled`), mode selector (`attendance_mode` —
  two-option control, e.g. shadcn RadioGroup or Select: "Fixed Schedule" /
  "Flexible Hours", each with a one-line helper caption explaining the
  difference), time picker (`work_start_time` — label changes based on
  selected mode: "Work start time" for Fixed, "Daily reminder time" for
  Flexible), number input (`daily_required_hours`, hours with 2 decimal
  places, `font-mono` per RULE F-11 since it's numeric data), day-of-week
  checkboxes (`off_days`).
- All fields disabled/grayed when `attendance_enabled` is OFF, consistent
  with standard disabled-dependent-field UX (no new pattern needed).

### 6.3 Workspace Settings — Billable Toggle

- New toggle (`is_billable`) in existing Workspace Settings, General
  section (or a new "Billing" section if cleaner — build agent's
  discretion, flag for confirmation if ambiguous).
- On toggle OFF: shadcn AlertDialog confirmation ("Projects and tasks will
  no longer be billable. Existing rate data will be preserved. Continue?")
  before committing — this is a meaningful workspace-wide behavior change
  and warrants confirmation, consistent with RULE F-09 patterns for
  destructive/significant actions even though no data is destroyed.

### 6.4 Timer Bar — Daily Progress Badge

- New small badge element in the existing Timer Bar (Phase 4 component),
  visible only for Member role, only when both `attendance_enabled` and
  `daily_required_hours` are active.
- Format: `font-mono` (RULE F-11), e.g. `"3.2h / 5h"`.
- Default state: neutral/muted styling. Warning state: switches to a
  warning color token (not raw hex — use existing semantic warning token if
  one exists in the design system; flag for confirmation if it doesn't).
- Exact pacing threshold formula for triggering warning state is an open
  question — see §8.

### 6.5 Stop Timer / Log Out — Confirmation AlertDialogs

- Two new AlertDialog instances (or one shared component with a variant
  prop) reusing the existing AlertDialog pattern, copy: "You've logged
  {X.X}h of {Y}h today. {Stop tracking / Log out} anyway?"
- Triggered conditionally inside the existing Stop Timer mutation and
  existing Log Out flow — not new pages, just new conditional UI states on
  existing actions.

### 6.6 Browser Tab-Close Warning

- Standard browser `beforeunload` native prompt (cannot be styled — this is
  a browser-native UI, not a custom component). See §8 for the known
  limitation that modern browsers show generic text regardless of what
  string is set, by design (anti-abuse browser behavior).

### 6.7 Notification Bell / Sheet — New Notification Types

- Two new notification type renderings inside the existing Notification
  Sheet (Phase 6 component): "missed work start" (self) and "daily hours
  shortfall" (Admin/Manager view, showing which Member and which date).
- Follows existing notification list item pattern — no new list mechanism.

### 6.8 Notification Settings — Push Permission Toggle

- New toggle in the existing Profile/Notification Settings screen:
  "Enable push notifications" — triggers the browser permission request on
  toggle ON, calls `POST /users/me/push-subscriptions` on grant.
- Shows current permission state (granted/denied/not-requested) per
  standard browser permission UX patterns.

---

## 7. OUT-OF-SCOPE ITEMS (EXPLICITLY LOGGED)

Per Constraint 3 (Scope Integrity), these are logged to the post-MVP
backlog rather than silently expanded into this addendum:

| Item | Why Out of Scope Now |
|------|----------------------|
| True OS-level idle detection (cross-application, browser-independent) | Technically impossible in a web browser; requires the native Desktop App (Electron/Tauri) |
| Desktop app auto-start on boot | Desktop-app-only concept; no web equivalent exists |
| Per-member daily hour targets / per-member work-start times | Human supervisor explicitly chose "one global number per workspace" |
| Per-member attendance mode (mixing Fixed Schedule and Flexible Hours within one workspace) | Human supervisor explicitly chose "Admin picks ONE mode for the whole workspace" — confirmed 2026-06-21 |
| Manager-to-member direct-report assignment | Confirmed: no such concept exists; Manager role remains workspace-wide for this feature, consistent with existing approval workflow permissions |
| Re-prompting Members who ignore the work-start modal | Confirmed: notify once only, no re-prompt |
| Per-member exemption from attendance tracking (e.g. part-time toggle) | Confirmed: applies to all Members automatically, no opt-out |

---

## 8. OPEN RISK NOTES — MUST BE RESOLVED IN PHASE 6.5 STEP 1, BEFORE CODING

These are not yet decided. The build agent must STOP and ask before writing
related code, per Constraint 4 (Clarity Before Code). Listed here so they
are not lost between this conversation and the build session.

1. **Exact timezone field name and location.** This addendum assumes a
   timezone field exists somewhere reachable per-Member (human supervisor
   said "each workspace member has a timezone"). The exact column
   (`workspaces.timezone`? `users.timezone`? both, with one overriding the
   other?) must be confirmed against the live DB Schema document before
   any scheduler or trigger-time logic is written. If no such field
   actually exists, this is a NEW field that must be added and is a
   blocking dependency for F1 and F2 entirely.

2. **Dedicated `attendance_notifications` table vs. extending the existing
   Phase 6 `notifications` table.** §3.2 proposes a new table provisionally.
   Before building, check whether the existing Phase 6 notifications schema
   can represent these two new notification types (self-targeted vs.
   role-broadcast) without the dedicated table. Prefer reuse if it fits
   cleanly; the dedicated table is the fallback, not the default.

3. **Pacing/warning-state formula for the Timer Bar daily progress badge**
   (§6.4). "Turns red when behind pace" needs a concrete formula — e.g.
   comparing hours-logged-so-far against expected-hours-by-current-time-of-
   day, assuming an even distribution across the work_start_time-to-now
   window. This needs a decision before the component can be built, not
   left to the build agent's invention (Constraint 1 — No Hallucination
   applies to UI logic too, not just backend rules).

4. **`beforeunload` browser limitation.** Modern browsers (Chrome, Firefox,
   Safari) ignore any custom string passed to `beforeunload` and show a
   generic browser-controlled message ("Leave site? Changes you made may
   not be saved.") for anti-abuse reasons. This means the exact copy
   "You've logged 3.2/5h today" CANNOT appear in the tab-close warning —
   only in the Stop Timer / Log Out AlertDialogs, which are fully
   custom and unaffected by this limitation. The human supervisor should
   be aware the tab-close case will look generic, not custom-branded.

5. **APScheduler + multi-instance deployment risk.** If AWS ECS Fargate
   ever runs more than one instance of the backend (not currently
   documented as planned, per TRD §5 single-service description, but worth
   flagging), in-process APScheduler would fire the same job redundantly
   on each instance. Not a problem at current single-instance MVP scale,
   but should be noted as a reason to revisit the scheduler architecture
   if horizontal scaling is ever introduced.

6. **`IdleDetector` browser support drift.** Browser support for this API
   should be re-verified at implementation time (web search, not training
   data) since vendor positions on experimental APIs can change.

---

*End of Addendum v1.0. This document, once approved, becomes Priority-level
documentation equivalent to the base PRD/TRD/Schema/API/Blueprint documents
for all Phase 6.5 work, per the Documentation Hierarchy in the Phase 6.5
session prompt.*
