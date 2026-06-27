# Yusi Time — Project State
**Last Updated:** 2026-06-21 — Phase 6.5 Step 6.5.1 In Progress
**Current Phase:** Phase 6.5 — Attendance, Hours Target, Billable Toggle & Idle Detection — 🔄 In Progress
**Last Session Summary:** Phase 6 (Approvals & Notifications) fully implemented and verified. Frontend React Query hooks built for querying notifications and approving timesheets. Notification Bell badges properly display unread counts with framer motion spring animations. Approval workflow features including Quick Approve and Quick Reject UI are fully functional. Ready to initialize Phase 7.

---

## Phase Summary Table

| Phase | Name | Status | Date Completed |
|-------|------|--------|----------------|
| 0 | Setup & Infrastructure | ✅ Completed | 2026-05-29 |
| 1 | Authentication | ✅ Completed | 2026-05-31 |
| 1.5 | Super Admin Backend (API-only) | ✅ Completed | 2026-05-31 |
| 2 | Workspace & Members | ✅ Completed | 2026-06-01 |
| 3 | Projects, Tasks, Clients, Tags | ✅ Completed | 2026-06-02 |
| 4 | Time Tracking Core | ✅ Completed | 2026-06-18 |
| 5 | Continue, Duplicate & Draft | ✅ Completed | 2026-06-18 |
| 6 | Approvals & Notifications | ✅ Completed | 2026-06-21 |
| 6.5 | Attendance, Hours Target, Billable Toggle & Idle Detection | 🔄 In Progress | — |
| 7 | Reports & Analytics | ⬜ Not Started | — |
| 7.5 | Super Admin UI Dashboard | ⬜ Not Started | — |
| 8 | Webhooks, Polish & Deploy | ⬜ Not Started | — |

**Status legend:** ⬜ Not Started | 🔄 In Progress | ✅ Completed | ❌ Blocked

---

## Current Phase Detail

### Phase 6.5 — Attendance, Hours Target, Billable Toggle & Idle Detection — 🔄 In Progress

#### Steps Completed
- [x] Step 6.5.1 — Backend Models & Alembic Migration
  - Created `attendance_notification.py` (Addendum §3.2)
  - Created `push_subscription.py` (Addendum §3.3)
  - Modified `workspace.py` — added 6 new columns: `attendance_enabled`, `attendance_mode`, `work_start_time`, `daily_required_hours`, `off_days`, `is_billable` (Addendum §3.1)
  - Created migration `20260621_2300_phase65_attendance_billable_push.py` — hand-written, upgrade+downgrade round-trip verified ✅
- [x] Step 6.5.2 — Backend Schemas & Config Updates
  - Created `schemas/attendance.py` — all 10 schemas: WorkspaceAttendanceSettingsUpdate/Response, WorkspaceBillableSettingsUpdate/Response, DailyProgressResponse, WorkStartRequest/Response, AttendanceNotificationResponse/ListResponse, PushSubscriptionCreate/Response (Addendum §4.1–4.5)
  - Updated `core/config.py` — added `vapid_public_key`, `vapid_private_key`, `vapid_claims_subject` Optional env vars (Addendum §5.3, RULE B-07)
- [x] Step 6.5.3 — Attendance Service (F1 + F2 business logic)
  - Created `services/attendance_service.py` — 7 functions: check_work_start_for_workspace, check_daily_shortfall_for_workspace, record_work_start_response, get_daily_progress, get_attendance_notifications, update_attendance_settings, update_billable_settings
  - All critical rules enforced: PRD-ADD-01 through PRD-ADD-08, Option B pacing formula
  - Timezone logic uses workspaces.default_timezone throughout (Risk 1 resolution)
- [x] Step 6.5.4 — Billable Service + Rate Service Patch (F3)
  - Modified `services/rate_service.py` — `is_billable` short-circuit at top of `resolve_rate()`: when `workspace.is_billable=False`, entire 4-level rate hierarchy returns `None` immediately without touching stored data (PRD-ADD-05, Addendum §2.4)
  - `update_attendance_settings()` and `update_billable_settings()` already implemented in Step 6.5.3 `attendance_service.py` (RULE B-06 layering: router → attendance_service directly)
  - Existing `hourly_rate_cents` on tasks/projects/clients/workspace preserved unchanged — no DELETE, no NULL-out (PRD-ADD-06 confirmed)
- [x] Step 6.5.5 — Scheduler Service (APScheduler integration)
  - Installed `apscheduler==3.10.4` via `poetry add`
  - Created `services/scheduler_service.py` — AsyncIOScheduler with 2 jobs: F1 (check_workspace_attendance) + F2 (check_daily_shortfall), both every 60s, max_instances=1, coalesce=True
  - Modified `app/main.py` — added `lifespan` context manager; scheduler starts on app startup, stops cleanly on shutdown (Addendum §5.2, RULE B-06)
  - Per-workspace error isolation in each job; push_service lazily imported (Step 6.5.6 adds it)
- [x] Step 6.5.6 — Web Push Service + Subscription Router
  - Installed `pywebpush==2.0.0` via `poetry add`
  - Created `services/push_service.py` — `send_work_start_push`, `create_subscription`, `delete_subscription`; sync pywebpush wrapped in `run_in_executor`; 410 Gone auto-removes stale subscriptions; VAPID-optional (graceful skip in dev)
  - Created `routers/push_subscriptions.py` — `POST /users/me/push-subscriptions` (upsert), `DELETE /users/me/push-subscriptions/{id}`
  - Registered `push_subscriptions_router` in `main.py`
- [x] Step 6.5.7 — Attendance & Billable Settings Router
  - Created `routers/attendance.py` — 5 endpoints: `PATCH /workspaces/{id}/attendance-settings`, `PATCH /workspaces/{id}/billable-settings`, `GET /time-entries/daily-progress`, `POST /time-entries/work-start-response`, `GET /notifications/attendance`
  - `work_start_response` correctly delegates timer creation to `time_entry_service.start_timer()` (RULE B-06)
  - Registered `attendance_router` in `main.py`
- [x] Step 6.5.8 — Phase 6.5 Backend Tests
  - Created `tests/unit/test_attendance_service.py` — 34 unit tests across 6 test classes covering all PRD-ADD rules (01–08), Option B pacing formula, `record_work_start_response`, and settings updates
  - Created `tests/unit/test_rate_service_billable.py` — 10 unit tests for `is_billable` short-circuit (PRD-ADD-05) and rate hierarchy (PRD-ADD-06 data preservation)
  - Created `tests/integration/test_attendance.py` — 20 integration tests for all 5 attendance endpoints + push subscription CRUD (require test DB on port 5433)
  - Unit tests: **34/34 PASSED** ✅; Integration tests: require test DB (same constraint as all other integration tests)
- [x] Step 6.5.9 — Frontend API Layer & Hooks
  - Created `features/attendance/api.ts` — 7 API functions with full TypeScript types for all Phase 6.5 endpoints
  - Created `features/attendance/hooks/useAttendance.ts` — 6 hooks: `useUpdateAttendanceSettings`, `useUpdateBillableSettings`, `useDailyProgress` (30s poll), `useWorkStartResponse`, `useAttendanceNotifications` (30s poll), `usePushSubscription`
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.10 — Work Start Prompt Modal (F1, both modes)
  - Created `stores/attendance-store.ts` — Zustand store with `openWorkStart`/`closeWorkStart` + `WorkStartContext` (mode + late_by_minutes)
  - Created `features/attendance/components/WorkStartModal.tsx` — non-dismissible F1 modal; Fixed Schedule (on-time + late variants) + Flexible Hours copy; inline project selector on "Start Tracking"; "Not Now" creates notification via API
  - Created `features/attendance/hooks/useWorkStartTrigger.ts` — polls attendance notifications (30s), opens modal when unread today's `work_start_missed` found; deduplication via `useRef<Set<string>>` to prevent re-open
  - Created `features/attendance/components/AttendanceController.tsx` — layout-level wrapper that reads workspace attendance settings and mounts trigger + modal
  - Extended `WorkspaceDetail` in `settings/api.ts` with all Phase 6.5 attendance+billable fields
  - Mounted `<AttendanceController>` in `(app)/layout.tsx` alongside `<IdleModal>`
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.11 — Timer Bar Daily Progress Badge (F2)
  - Added `useDailyProgress` call to `TimerBar.tsx` (Member-only, 30s poll, disabled for Admin/Manager)
  - Role derived from `useWorkspaces()` list — finds active workspace entry's `.role` field
  - Badge only renders when `isMember && attendanceEnabled && daily_required_hours != null`
  - Two visual states: emerald (on_pace=true) / amber (on_pace=false, Option B formula)
  - Format: `font-mono` `"3.2h / 5h"` with dot indicator + tooltip showing pace status
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.12 — Stop Timer & Log Out Confirmation AlertDialogs (F2)
  - **Stop Timer guard**: Intercepted `handleStop` in `TimerBar.tsx` — checks `isMember && attendanceEnabled && hours_logged < daily_required_hours`; shows "Stop tracking early?" AlertDialog with "Keep Tracking" / "Stop Anyway"
  - **Log Out guard**: Extended `attendance-store.ts` with `logoutGuardOpen`/`openLogoutGuard`/`closeLogoutGuard`/`pendingLogout`; created `LogoutGuardDialog.tsx`; intercepted `handleLogout` in layout to call `openLogoutGuard()` with `doLogout` callback when below target
  - **Tab-close guard (Case 3)**: Created `useBeforeUnloadGuard.ts`; wired into layout; attaches native `beforeunload` event when Member has active timer + below target; acknowledges browser limitation (generic text shown, not custom string)
  - All three guards are Member-only (`role==='member'`), suppressed when `attendanceEnabled=false` or `daily_required_hours=null`
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.13 — Workspace Settings UI
  - **Section 4 — Attendance & Schedule** (new Card): master toggle (`attendance_enabled`), mode selector (Fixed Schedule / Flexible Hours with dynamic description), work start time / daily reminder time (HTML time input, onBlur PATCH), daily hour target (number input, onBlur PATCH), off days (day-of-week pill buttons, instant PATCH), OS idle detection info note (Addendum §2.5 honest limitation)
  - **Section 5 — Billing** (new Card): `is_billable` toggle; disabling shows AlertDialog confirmation ("Existing rate data preserved") before calling PATCH
  - All Attendance fields gray/disabled when `attendanceEnabled=false` (Addendum §6.2)
  - Attendance + billable mutations fire immediately on change (no deferred Save button) — separate from general workspace settings
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.14 — Notification Bell — New Attendance Types
  - Rewrote `NotificationBell.tsx` — merged two streams (`notifications` + `attendance_notifications`) into a single `UnifiedItem` shape sorted DESC by `created_at`
  - Badge count = `regularUnread + attUnread` (combined)
  - scope auto-selected: `'self'` for Member, `'managed'` for Admin/Manager
  - Attendance stream only fetched when `attendanceEnabled=true` (no 403s for non-attendance workspaces)
  - New icons: `AlarmClock` (work_start_missed), `Timer` (flexible_reminder_missed), `TrendingDown` (daily_hours_shortfall)
  - Amber accent line on unread attendance items vs orange for regular
  - Auto-generated title/message copy for all 3 attendance types including late_by_minutes and hours_logged context
  - Small "Attendance" badge chip on each attendance item for visual provenance
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.15 — Enhanced Idle Detection (F4)
  - Rewrote `useIdleDetector.ts` — orchestrates native vs fallback: tries `window.IdleDetector` (Chrome 94+/Edge 94+) first via AbortController; falls back to existing event-based logic with zero behavioral regression (PRD-ADD-07)
  - Exported `requestNativeIdlePermission()` — called inside `TimerBar.doStartTimer` (user gesture context); no-ops on unsupported browsers/denied permission
  - `IdleModal` and its 3 options unchanged — only detection signal source changes (spec §2.5)
  - Permission NOT bundled with push notification permission (spec §2.5)
  - `nativeStarted` flag: if `detector.start()` throws `NotAllowedError` (permission denied) or any error, falls back to event-based immediately
  - Workspace settings already has the honest limitation note (Chrome/Edge only) from Step 6.5.13
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.16 — Push Service Worker + Permission Toggle
  - Created `web/public/sw.js` — service worker with `push` event handler (JSON payload: title/body/icon/tag/url), `notificationclick` (focus existing tab or open new), `install`/`activate` with skipWaiting + claim
  - Created `features/attendance/hooks/usePushNotifications.ts` — orchestrates SW registration → permission request → PushManager.subscribe → backend POST; disable path calls PushManager.unsubscribe + backend DELETE; VAPID key from `NEXT_PUBLIC_VAPID_PUBLIC_KEY` env var
  - Added Notifications card to `settings/profile/page.tsx` — Switch + 4-state permission chip (Active / Blocked / Unsupported / Not enabled); disabled when denied/unsupported; `onCheckedChange` IS the user gesture (no auto-request on page load per Addendum §6.8)
  - `tsc --noEmit` ✅ zero errors
- [x] Step 6.5.17 — Phase 6.5 Frontend Verification & Final Checklist
  - Final `tsc --noEmit` across entire `web/` project ✅ zero errors
  - All 17 steps verified against Addendum v1
  - Full walkthrough written to `walkthrough.md`

#### Steps Remaining
_None — Phase 6.5 implementation complete_ ✅
#### Risk Clearance Decisions (resolved 2026-06-21)
- Risk 1 (timezone): scheduler uses `workspaces.default_timezone` for all time conversions
- Risk 2 (notifications): dedicated `attendance_notifications` table approved
- Risk 3 (warning formula): Option B — impossibility check (`seconds_until_midnight < required - logged`)

---

### Phase 6 — Approvals & Notifications — ✅ Completed

#### Steps Completed
- [x] Step 6.1 — Backend Models: Created `timesheet_submission.py` and `submission_entry.py` to represent submissions safely and immutable state.
- [x] Step 6.2 — Backend Services & Routers: Implemented `approval_service.py` and `notification_service.py` with full logic for submission generation, approval, rejection, and notification broadcast.
- [x] Step 6.3 — Phase 6 Tests: Added `test_approvals.py`, `test_approval_service.py`, and `test_notification_service.py` achieving 100% test pass rate for integration logic.
- [x] Step 6.4 — Frontend API & Hooks: Implemented React Query hooks (`useApprovals`, `useNotifications`) with 3-second real-time polling intervals for snappy UX.
- [x] Step 6.5 — Frontend Approvals UI: Built `ApprovalList.tsx` and `SubmissionDetailsSheet.tsx` providing Quick Approve/Reject actions and detailed breakdown views.
- [x] Step 6.6 — Frontend Notifications UI: Redesigned the `NotificationBell.tsx` to use a modern `Popover` interface with glassmorphism, Framer Motion staggered animations, and `ScrollArea` bounds enforcement.

#### Decisions Made
- Migrated the Notification UI from a full-page side `Sheet` drawer to a contextual `Popover` floating menu to improve aesthetics.
- Dropped long-polling/WebSockets in favor of aggressive 3-second polling on notifications for near real-time UX without additional infrastructure complexity.

#### Issues / Bugs Discovered and Resolved
- Fixed Radix `ScrollArea` flex-box height infinite-growth bug by enforcing strict `min-h-0` boundaries.
- Resolved Base UI `asChild` prop deprecation conflicts and Typescript type alignment within UI elements.
- Fixed `PopoverContent` absolute positioning overlap issues with internal `X` close buttons.
- Cleaned up lingering backend lint errors including unused imports and empty f-strings.

---

### Phase 5 — Continue, Duplicate & Draft — ✅ Completed

#### Steps Completed
- [x] Step 5.1 — Backend Models & Drafts: Validated drafts field length and handled frontend draft syncing.
- [x] Step 5.2 — Backend Endpoints (Continue & Duplicate): Implemented endpoints with fresh rate fetching, force-stop logic, and proper midnight alignment for duplication.
- [x] Step 5.3 — Phase 5 Tests: Added comprehensive testing for continue/duplicate logic including rounding rule checks and force-stop behavior.
- [x] Step 5.4 — Frontend API & Hooks: Implemented `useContinueEntry` and `useDuplicateEntry` mutations.
- [x] Step 5.5 — Frontend UI Integration: Built `ContinueButton` and `DuplicateMenuItem`. Wired `ContinueButton` securely into the Dashboard UI. 

#### Decisions Made
- Duplication always calculates a fresh hourly rate from the database instead of inheriting the source entry's historical rate.
- Duplicate and Continue actions return `null` instead of rendering a disabled button for entries with a `pending` status to prevent UI ambiguity.
- The `DuplicateMenuItem` component is built but explicitly waiting for Phase 7 tables to be rendered since current tables don't use Dropdown Menus.

#### Issues / Bugs Discovered and Resolved
- Fixed `ContinueButton` Base UI TooltipTrigger structure to use `render={<button/>}` due to Base UI v1 deprecating `asChild`.
- Fixed `TimerBar.tsx` not properly synchronizing Project/Task dropdowns when forcing a new entry via the Continue action.

---

### Phase 4 — Time Tracking Core — ✅ Completed

#### Steps Completed
- [x] Step 4.1 — Backend Time Entry CRUD: Basic CRUD + Rounding Logic + Billable computations.
- [x] Step 4.2 — Backend Timer Actions: start, stop, discard endpoints and validations.
- [x] Step 4.3 — Phase 4 Backend Tests.
- [x] Step 4.4 — Timer Store & Hooks: Centralized running timer logic.
- [x] Step 4.5 — Timer Bar UI.
- [x] Step 4.6 — Idle Detection Modal: Intercepts AFK timers.
- [x] Step 4.7 — Manual Entry Modal.
- [x] Step 4.8 — Dashboard UI.
- [x] Step 4.9 — Timesheet Grid UI.

#### Decisions Made
- Abstracted all rounding rules into a pure `rounding_service` ensuring the backend *never* saves raw seconds.

#### Issues / Bugs Discovered and Resolved
- Handled overlapping timers manually through standard `stop_timer` intercepting mechanisms.

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
