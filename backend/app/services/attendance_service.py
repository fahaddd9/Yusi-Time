"""
Attendance Service — Phase 6.5, Addendum §2.2 (F1), §2.3 (F2).

Functions:
  check_work_start_for_workspace()   — F1: per-member prompt evaluation, both modes
  check_daily_shortfall_for_workspace() — F2: midnight shortfall calculation
  record_work_start_response()       — F1: handles "start"/"not_now" response
  get_daily_progress()               — F2: Option B pace check for timer bar badge
  get_attendance_notifications()     — paginated list with recipient scope

Critical rules enforced here (Addendum §2):
  PRD-ADD-01: attendance_enabled is the master switch; if false, nothing runs.
  PRD-ADD-02: work_start_time or daily_required_hours can be null independently.
  PRD-ADD-02b: attendance_mode determines F1 variant (fixed_schedule / flexible_hours).
  PRD-ADD-03: F1 and F2 apply to Member role ONLY — Admin/Manager are exempt.
  PRD-ADD-04: F1 and F2 are suspended entirely on off_days.
  PRD-ADD-08: Flexible Hours reminder fires ONLY when Member has logged zero hours
              that day; suppressed entirely if any time was logged.

Option B pacing formula (Risk 3 resolution, approved 2026-06-21):
  on_pace = True  when seconds_until_midnight >= (required_seconds - logged_seconds)
            i.e. still mathematically possible to hit target by working non-stop.
  on_pace = True  when attendance_enabled=False or daily_required_hours=None.
"""

from __future__ import annotations

import uuid
import zoneinfo
import logging
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_notification import AttendanceNotification
from app.models.time_entry import TimeEntry
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.user import User

logger = logging.getLogger(__name__)

# ── Internal helpers ────────────────────────────────────────────────────────────

def _get_workspace_tz(workspace: Workspace) -> dt_timezone | zoneinfo.ZoneInfo:
    """
    Return timezone object for workspace.default_timezone.
    Risk 1 resolution (2026-06-21): all scheduler/trigger logic uses
    workspaces.default_timezone, not users.timezone.
    """
    tz_name = workspace.default_timezone or "UTC"
    if tz_name == "UTC":
        return dt_timezone.utc
    return zoneinfo.ZoneInfo(tz_name)


def _today_in_tz(tz: dt_timezone | zoneinfo.ZoneInfo) -> date:
    """Return the current calendar date in the given timezone."""
    return datetime.now(tz=tz).date()


def _now_in_tz(tz: dt_timezone | zoneinfo.ZoneInfo) -> datetime:
    """Return the current datetime (timezone-aware) in the given timezone."""
    return datetime.now(tz=tz)


def _is_off_day(workspace: Workspace, d: date) -> bool:
    """
    Return True if the given date falls on a workspace off_day.
    Addendum §2.1, PRD-ADD-04: 0=Sunday, 1=Monday, ..., 6=Saturday.
    Python weekday(): Monday=0, ..., Sunday=6 → needs conversion.
    """
    off_days: list[int] = workspace.off_days or [0]
    # Convert Python's weekday() (Mon=0..Sun=6) → Addendum convention (Sun=0..Sat=6)
    python_weekday = d.weekday()  # Mon=0, Tue=1, ..., Sun=6
    addendum_day = (python_weekday + 1) % 7  # Mon=1, ..., Sat=6, Sun=0
    return addendum_day in off_days


async def _get_hours_logged_today(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    calendar_date: date,
    tz: dt_timezone | zoneinfo.ZoneInfo,
) -> float:
    """
    Sum all time entry duration_seconds for a user on a calendar_date.
    Addendum §2.3: includes ALL statuses, ALL projects.
    Running entries (null duration_seconds) are excluded from completed totals
    but counted via their elapsed seconds if they started today.
    Returns total hours as a float.
    """
    # UTC boundaries for the calendar day in the workspace timezone
    day_start_local = datetime.combine(calendar_date, time.min).replace(tzinfo=tz)
    day_end_local = datetime.combine(calendar_date, time.max).replace(tzinfo=tz)
    day_start_utc = day_start_local.astimezone(dt_timezone.utc)
    day_end_utc = day_end_local.astimezone(dt_timezone.utc)

    # Sum completed (non-running) entries — duration_seconds IS NOT NULL
    stmt_completed = select(func.coalesce(func.sum(TimeEntry.duration_seconds), 0)).where(
        and_(
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.user_id == user_id,
            TimeEntry.start_time >= day_start_utc,
            TimeEntry.start_time <= day_end_utc,
            TimeEntry.duration_seconds.is_not(None),
        )
    )
    completed_seconds: int = await db.scalar(stmt_completed) or 0

    # Also count any currently-running entry that started today
    stmt_running = select(TimeEntry).where(
        and_(
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.user_id == user_id,
            TimeEntry.status == "running",
            TimeEntry.start_time >= day_start_utc,
            TimeEntry.start_time <= day_end_utc,
        )
    )
    running_entry = await db.scalar(stmt_running)
    running_seconds = 0
    if running_entry is not None:
        elapsed = datetime.now(tz=dt_timezone.utc) - running_entry.start_time.replace(tzinfo=dt_timezone.utc)
        running_seconds = max(0, int(elapsed.total_seconds()))

    total_seconds = completed_seconds + running_seconds
    return round(total_seconds / 3600, 4)


async def _has_any_time_entry_today(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    calendar_date: date,
    tz: dt_timezone | zoneinfo.ZoneInfo,
) -> bool:
    """
    Return True if the Member has ANY time entry (any status) starting today.
    Used by F1 Fixed Schedule trigger check (Addendum §2.2).
    """
    day_start_local = datetime.combine(calendar_date, time.min).replace(tzinfo=tz)
    day_end_local = datetime.combine(calendar_date, time.max).replace(tzinfo=tz)
    day_start_utc = day_start_local.astimezone(dt_timezone.utc)
    day_end_utc = day_end_local.astimezone(dt_timezone.utc)

    stmt = select(TimeEntry.id).where(
        and_(
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.user_id == user_id,
            TimeEntry.start_time >= day_start_utc,
            TimeEntry.start_time <= day_end_utc,
        )
    ).limit(1)
    result = await db.scalar(stmt)
    return result is not None


async def _already_notified_today(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_type: str,
    calendar_date: date,
) -> bool:
    """
    Guard against re-prompting (Addendum §2.2 "No re-prompt, both modes").
    Returns True if an attendance_notification of this type was already created
    for this user on this date.
    """
    stmt = select(AttendanceNotification.id).where(
        and_(
            AttendanceNotification.workspace_id == workspace_id,
            AttendanceNotification.user_id == user_id,
            AttendanceNotification.notification_type == notification_type,
            AttendanceNotification.related_date == calendar_date,
        )
    ).limit(1)
    result = await db.scalar(stmt)
    return result is not None


# ── Public API: F1 — Work Start Check ──────────────────────────────────────────

async def check_work_start_for_workspace(
    db: AsyncSession,
    workspace: Workspace,
    members: list[WorkspaceMember],
) -> list[uuid.UUID]:
    """
    F1 — Evaluate whether the work-start prompt should fire for each Member.
    Called by scheduler every minute per workspace.
    Addendum §2.2 (trigger logic, both modes), PRD-ADD-01 through PRD-ADD-04, PRD-ADD-08.

    Returns list of user_ids for which a notification record was created
    (i.e., Members who need to be prompted). The scheduler/push service
    uses this to send push notifications (Step 6.5.6).

    PRD-ADD-03: Only Member role is evaluated — Admin/Manager are skipped.
    PRD-ADD-04: Off-days suspended entirely.
    """
    if not workspace.attendance_enabled or workspace.work_start_time is None:
        return []  # PRD-ADD-01: master switch; PRD-ADD-02: independent null check

    tz = _get_workspace_tz(workspace)
    now = _now_in_tz(tz)
    today = now.date()

    if _is_off_day(workspace, today):
        return []  # PRD-ADD-04: suspended on off_days

    # Check if current time is within a 5-minute catch-up window of work_start_time.
    # This prevents missed notifications if the scheduler or user login is delayed.
    work_start: time = workspace.work_start_time  # type: ignore[assignment]
    now_minutes = now.hour * 60 + now.minute
    start_minutes = work_start.hour * 60 + work_start.minute
    
    # Handle midnight wraparound (if now_minutes is 1 and start_minutes is 1439)
    diff = now_minutes - start_minutes
    if diff < 0:
        diff += 24 * 60
        
    if diff > 5:
        return []  # Not trigger time yet, or window has passed

    notified_user_ids: list[uuid.UUID] = []
    attendance_mode = workspace.attendance_mode

    for member in members:
        # PRD-ADD-03: Members only — skip Admin and Manager
        if member.role in ("admin", "manager"):
            continue

        # Determine the notification type for this mode
        notif_type = (
            "work_start_missed"
            if attendance_mode == "fixed_schedule"
            else "flexible_reminder_missed"
        )

        # No re-prompt guard (Addendum §2.2)
        if await _already_notified_today(db, workspace.id, member.user_id, notif_type, today):
            continue

        if attendance_mode == "fixed_schedule":
            # Fixed Schedule: fires if Member has NO time entry today
            if await _has_any_time_entry_today(db, workspace.id, member.user_id, today, tz):
                continue  # Already started — no prompt needed

        else:
            # Flexible Hours: fires ONLY if Member has logged ZERO hours today
            # PRD-ADD-08: suppress even 0.01h is sufficient to suppress
            hours_logged = await _get_hours_logged_today(db, workspace.id, member.user_id, today, tz)
            if hours_logged > 0:
                continue  # PRD-ADD-08: any time logged → suppress reminder

        # Compute late_by_minutes: if diff > 0 the member is late by that many minutes.
        # diff == 0 means they are on-time (exact minute match).
        computed_late_minutes = diff if (diff > 0 and attendance_mode == "fixed_schedule") else None

        # Create the attendance notification record
        notif = AttendanceNotification(
            workspace_id=workspace.id,
            user_id=member.user_id,
            notification_type=notif_type,
            recipient_user_id=member.user_id,  # self-targeted (Addendum §3.2)
            related_date=today,
            late_by_minutes=computed_late_minutes,
            hours_logged=None,
        )
        db.add(notif)
        notified_user_ids.append(member.user_id)

    return notified_user_ids


# ── Public API: F2 — Daily Shortfall Check ─────────────────────────────────────

async def check_daily_shortfall_for_workspace(
    db: AsyncSession,
    workspace: Workspace,
    members: list[WorkspaceMember],
    check_date: date,
) -> list[AttendanceNotification]:
    """
    F2 — End-of-day shortfall check. Called by scheduler when midnight passes.
    Addendum §2.3, PRD-ADD-01, PRD-ADD-03, PRD-ADD-04.

    For each Member, if their total logged hours on check_date is less than
    daily_required_hours, creates one notification per Admin and per Manager
    in the workspace (role-broadcast — no direct-report model, Addendum §2.3).

    check_date: the calendar day that just ended (yesterday in the workspace tz).
    Returns all created AttendanceNotification records.
    """
    if not workspace.attendance_enabled or workspace.daily_required_hours is None:
        return []  # PRD-ADD-01: master switch; PRD-ADD-02: independent null check

    tz = _get_workspace_tz(workspace)

    if _is_off_day(workspace, check_date):
        return []  # PRD-ADD-04: suspended on off_days

    required_hours: float = float(workspace.daily_required_hours)

    # Collect Admins and Managers as recipients (Addendum §2.3)
    recipients = [m for m in members if m.role in ("admin", "manager")]
    if not recipients:
        return []  # No one to notify — unusual but safe to skip

    created: list[AttendanceNotification] = []

    for member in members:
        # PRD-ADD-03: Only check Member role — Admin/Manager's own time is exempt
        if member.role in ("admin", "manager"):
            continue

        hours_logged = await _get_hours_logged_today(
            db, workspace.id, member.user_id, check_date, tz
        )

        if hours_logged >= required_hours:
            continue  # Target met — no notification

        # One notification per recipient (Admin/Manager) — role-broadcast
        for recipient in recipients:
            notif = AttendanceNotification(
                workspace_id=workspace.id,
                user_id=member.user_id,       # Subject member who missed hours
                notification_type="daily_hours_shortfall",
                recipient_user_id=recipient.user_id,  # Admin/Manager recipient
                related_date=check_date,
                late_by_minutes=None,
                hours_logged=round(hours_logged, 2),
            )
            db.add(notif)
            created.append(notif)

    return created


# ── Public API: F1 — Work Start Response ───────────────────────────────────────

async def record_work_start_response(
    db: AsyncSession,
    workspace: Workspace,
    user_id: uuid.UUID,
    response: Literal["start", "not_now"],
    project_id: uuid.UUID | None,
    task_id: uuid.UUID | None,
) -> dict:
    """
    F1 — Handle Member's response to the work-start modal.
    Addendum §4.2, §2.2.

    response="start":
      - Delegates time entry creation to time_entry_service.start_timer()
        (called by the router, not here — service stays layered per RULE B-06)
      - Returns {"acknowledged": True, "time_entry_id": <uuid>, "message": "..."}

    response="not_now":
      - Creates an attendance_notification with the appropriate type for this mode.
      - Computes late_by_minutes by comparing now() to work_start_time in workspace tz.
        Fixed Schedule only — Flexible Hours has no lateness concept (Addendum §2.2).
      - Returns {"acknowledged": True, "time_entry_id": None, "message": "..."}

    This function handles only the "not_now" path (notification creation + late calc).
    The "start" path timer creation is orchestrated by the router which calls
    time_entry_service.start_timer() after this returns.
    """
    tz = _get_workspace_tz(workspace)
    now = _now_in_tz(tz)
    today = now.date()

    if response == "not_now":
        # Determine notification type from attendance_mode (Addendum §2.2)
        notif_type = (
            "work_start_missed"
            if workspace.attendance_mode == "fixed_schedule"
            else "flexible_reminder_missed"
        )

        # Compute late_by_minutes for Fixed Schedule mode (Addendum §2.2)
        late_by_minutes: int | None = None
        if (
            workspace.attendance_mode == "fixed_schedule"
            and workspace.work_start_time is not None
        ):
            work_start_today = datetime.combine(today, workspace.work_start_time, tzinfo=tz)
            if now > work_start_today:
                late_by_minutes = int((now - work_start_today).total_seconds() // 60)

        # Find unread notification and mark as read
        stmt = select(AttendanceNotification).where(
            and_(
                AttendanceNotification.workspace_id == workspace.id,
                AttendanceNotification.recipient_user_id == user_id,
                AttendanceNotification.notification_type == notif_type,
                AttendanceNotification.related_date == today,
                AttendanceNotification.is_read.is_(False),
            )
        )
        unread_notifs = await db.scalars(stmt)
        notif_list = list(unread_notifs)
        if not notif_list:
            # If the frontend local timer fired before the cron job, create the notification
            # so the cron job's `_already_notified_today` guard correctly skips it.
            # We fetch managers/admins to be recipients.
            stmt_recipients = select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace.id,
                    WorkspaceMember.role.in_(["admin", "manager"])
                )
            )
            recipients = list(await db.scalars(stmt_recipients))
            for recipient in recipients:
                new_notif = AttendanceNotification(
                    workspace_id=workspace.id,
                    user_id=user_id,
                    notification_type=notif_type,
                    recipient_user_id=recipient.user_id,
                    related_date=today,
                    late_by_minutes=late_by_minutes,
                    is_read=True
                )
                db.add(new_notif)
        else:
            for unread in notif_list:
                unread.is_read = True
                if late_by_minutes is not None:
                    unread.late_by_minutes = late_by_minutes

        return {
            "acknowledged": True,
            "time_entry_id": None,
            "message": "Reminder dismissed. We'll check in again tomorrow.",
        }

    # response="start"
    notif_type = (
        "work_start_missed"
        if workspace.attendance_mode == "fixed_schedule"
        else "flexible_reminder_missed"
    )
    late_by_minutes = None
    if (
        workspace.attendance_mode == "fixed_schedule"
        and workspace.work_start_time is not None
    ):
        work_start_today = datetime.combine(today, workspace.work_start_time, tzinfo=tz)
        if now > work_start_today:
            late_by_minutes = int((now - work_start_today).total_seconds() // 60)

    stmt = select(AttendanceNotification).where(
        and_(
            AttendanceNotification.workspace_id == workspace.id,
            AttendanceNotification.recipient_user_id == user_id,
            AttendanceNotification.notification_type == notif_type,
            AttendanceNotification.related_date == today,
            AttendanceNotification.is_read.is_(False),
        )
    )
    unread_notifs = await db.scalars(stmt)
    notif_list = list(unread_notifs)
    if not notif_list:
        # Same as above, create dummy read notification so cron doesn't fire it later
        stmt_recipients = select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.role.in_(["admin", "manager"])
            )
        )
        recipients = list(await db.scalars(stmt_recipients))
        for recipient in recipients:
            new_notif = AttendanceNotification(
                workspace_id=workspace.id,
                user_id=user_id,
                notification_type=notif_type,
                recipient_user_id=recipient.user_id,
                related_date=today,
                late_by_minutes=late_by_minutes,
                is_read=True
            )
            db.add(new_notif)
    else:
        for unread in notif_list:
            unread.is_read = True
            if late_by_minutes is not None:
                unread.late_by_minutes = late_by_minutes

    return {
        "acknowledged": True,
        "time_entry_id": None,  # Router will populate from time_entry_service result
        "message": "Starting your timer now.",
    }


# ── Public API: F2 — Daily Progress ────────────────────────────────────────────

async def get_daily_progress(
    db: AsyncSession,
    workspace: Workspace,
    user_id: uuid.UUID,
) -> dict:
    """
    F2 — Live daily progress for the Timer Bar badge.
    Addendum §4.2, §6.4.

    Option B pacing formula (Risk 3 — approved 2026-06-21):
      on_pace = True  when it is still mathematically possible to hit the target
                       (seconds_until_midnight >= required_seconds - logged_seconds)
      on_pace = True  when target is not applicable (safe default for frontend)

    Returns dict matching DailyProgressResponse schema (Addendum §4.5).
    PRD-ADD-03: Only called for Member role — enforced in router.
    """
    # If attendance is off or no daily target, return clean "no indicator" response
    if not workspace.attendance_enabled or workspace.daily_required_hours is None:
        return {
            "hours_logged_today": 0.0,
            "daily_required_hours": None,
            "on_pace": True,  # Frontend renders no badge when daily_required_hours is None
        }

    tz = _get_workspace_tz(workspace)
    today = _today_in_tz(tz)
    now = _now_in_tz(tz)

    if _is_off_day(workspace, today):
        return {
            "hours_logged_today": 0.0,
            "daily_required_hours": None,
            "on_pace": True,
        }

    hours_logged = await _get_hours_logged_today(db, workspace.id, user_id, today, tz)
    required_hours: float = float(workspace.daily_required_hours)

    # Option B impossibility check: can Member still hit target working non-stop to midnight?
    # seconds_until_midnight = seconds from now until 23:59:59 of today
    midnight_today = datetime.combine(today + timedelta(days=1), time.min, tzinfo=tz)
    seconds_until_midnight = max(0, (midnight_today - now).total_seconds())
    required_seconds = required_hours * 3600
    logged_seconds = hours_logged * 3600
    remaining_seconds_needed = max(0, required_seconds - logged_seconds)

    # on_pace = True means "still possible" (or already met)
    on_pace = seconds_until_midnight >= remaining_seconds_needed

    return {
        "hours_logged_today": round(hours_logged, 2),
        "daily_required_hours": required_hours,
        "on_pace": on_pace,
    }


# ── Public API: Attendance Notifications List ───────────────────────────────────

async def get_attendance_notifications(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_user_id: uuid.UUID,
    caller_role: str,
    recipient_scope: Literal["self", "managed"],
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """
    GET /notifications/attendance — paginated attendance notifications.
    Addendum §4.4.

    recipient_scope="self": only notifications where recipient_user_id = caller
    recipient_scope="managed": all notifications in workspace (Admin/Manager only)
      — 403 if Member/Viewer requests managed scope (enforced in router).
    """
    if recipient_scope == "managed" and caller_role not in ("admin", "manager"):
        raise HTTPException(
            status_code=403,
            detail="Only Admin and Manager roles can view managed notifications",
            headers={"code": "FORBIDDEN"},
        )

    base_filter = [AttendanceNotification.workspace_id == workspace_id]

    if recipient_scope == "self":
        base_filter.append(AttendanceNotification.recipient_user_id == caller_user_id)
    # "managed" scope: no additional filter — all workspace attendance notifications

    # Count total and unread
    count_stmt = select(func.count()).select_from(AttendanceNotification).where(*base_filter)
    total: int = await db.scalar(count_stmt) or 0

    unread_filter = [*base_filter, AttendanceNotification.is_read.is_(False)]
    unread_stmt = select(func.count()).select_from(AttendanceNotification).where(*unread_filter)
    unread_count: int = await db.scalar(unread_stmt) or 0

    # Paginated data, newest first
    offset = (page - 1) * per_page
    data_stmt = (
        select(AttendanceNotification, User.full_name, Workspace.daily_required_hours)
        .join(User, AttendanceNotification.user_id == User.id)
        .join(Workspace, AttendanceNotification.workspace_id == Workspace.id)
        .where(*base_filter)
        .order_by(AttendanceNotification.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(data_stmt)
    rows = result.all()
    
    notifications = []
    for notif, user_full_name, daily_req in rows:
        # Dynamically set these fields on the model instance so Pydantic can read them
        setattr(notif, "user_full_name", user_full_name)
        setattr(notif, "daily_required_hours", float(daily_req) if daily_req is not None else None)
        notifications.append(notif)

    return {
        "data": notifications,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "per_page": per_page,
    }


async def mark_read(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_ids: list[uuid.UUID],
) -> None:
    """
    Mark specific attendance notifications as read.
    """
    from sqlalchemy import update
    
    if not notification_ids:
        return
        
    stmt = (
        update(AttendanceNotification)
        .where(
            AttendanceNotification.recipient_user_id == user_id,
            AttendanceNotification.id.in_(notification_ids),
            AttendanceNotification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    await db.execute(stmt)


async def mark_all_read(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """
    Mark all unread attendance notifications as read for a specific user in a workspace.
    """
    from sqlalchemy import update
    
    stmt = (
        update(AttendanceNotification)
        .where(
            AttendanceNotification.workspace_id == workspace_id,
            AttendanceNotification.recipient_user_id == user_id,
            AttendanceNotification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    await db.execute(stmt)


# ── Public API: Update Attendance Settings ──────────────────────────────────────

async def update_attendance_settings(
    db: AsyncSession,
    workspace: Workspace,
    attendance_enabled: bool | None,
    attendance_mode: str | None,
    work_start_time: str | None,  # "HH:MM" string from API
    daily_required_hours: float | None,
    off_days: list[int] | None,
) -> Workspace:
    """
    PATCH /workspaces/{id}/attendance-settings.
    Addendum §4.1 — Admin only (enforced in router).
    All fields are individually nullable (PATCH semantics).
    """
    if attendance_enabled is not None:
        workspace.attendance_enabled = attendance_enabled
    if attendance_mode is not None:
        workspace.attendance_mode = attendance_mode
    if work_start_time is not None:
        # Parse "HH:MM" to a time object for the TIME column
        h, m = map(int, work_start_time.split(":"))
        workspace.work_start_time = time(hour=h, minute=m)
    if daily_required_hours is not None:
        workspace.daily_required_hours = daily_required_hours
    if off_days is not None:
        workspace.off_days = off_days

    return workspace


async def update_billable_settings(
    db: AsyncSession,
    workspace: Workspace,
    is_billable: bool,
) -> Workspace:
    """
    PATCH /workspaces/{id}/billable-settings.
    Addendum §4.1, PRD-ADD-05, PRD-ADD-06.

    Toggling is_billable=False suppresses rate computation workspace-wide.
    Existing rate data (hourly_rate_cents on tasks/projects/clients/workspace)
    is NEVER deleted — preserved for when/if is_billable is restored (PRD-ADD-06).
    """
    workspace.is_billable = is_billable
    return workspace
