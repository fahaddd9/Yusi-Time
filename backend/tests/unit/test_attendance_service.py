"""
Unit tests for attendance_service.py — Phase 6.5, Addendum §2.2, §2.3.

Tests verify all critical business rules using mocked DB sessions:
  PRD-ADD-01: attendance_enabled master switch
  PRD-ADD-02: work_start_time / daily_required_hours independently nullable
  PRD-ADD-02b: attendance_mode mode-specific logic (fixed vs flexible)
  PRD-ADD-03: Member-only scope (Admin/Manager exempt from F1 and F2)
  PRD-ADD-04: off_days suspension
  PRD-ADD-08: Flexible Hours suppressed when any time logged
  Option B: pacing formula on_pace correctness
"""

import uuid
import pytest
from datetime import date, time, datetime, timezone as dt_timezone
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.attendance_notification import AttendanceNotification
from app.services.attendance_service import (
    check_work_start_for_workspace,
    check_daily_shortfall_for_workspace,
    get_daily_progress,
    record_work_start_response,
    update_attendance_settings,
    update_billable_settings,
)


# ── Fixtures ────────────────────────────────────────────────────────────────────

def make_workspace(
    attendance_enabled=True,
    attendance_mode="fixed_schedule",
    work_start_time=time(9, 0),
    daily_required_hours=8.0,
    off_days=None,      # None = [0] (Sunday only)
    default_timezone="UTC",
    is_billable=True,
):
    ws = MagicMock(spec=Workspace)
    ws.id = uuid.uuid4()
    ws.attendance_enabled = attendance_enabled
    ws.attendance_mode = attendance_mode
    ws.work_start_time = work_start_time
    ws.daily_required_hours = daily_required_hours
    ws.off_days = off_days if off_days is not None else [0]  # Sunday off by default
    ws.default_timezone = default_timezone
    ws.is_billable = is_billable
    ws.deleted_at = None
    return ws


def make_member(role="member"):
    m = MagicMock(spec=WorkspaceMember)
    m.user_id = uuid.uuid4()
    m.workspace_id = uuid.uuid4()
    m.role = role
    return m


def make_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    # Default scalar returns: no existing notification, zero hours
    db.scalar = AsyncMock(return_value=None)

    class MockResult:
        def __init__(self, items=None):
            self._items = items or []
        def scalars(self):
            class S:
                def __init__(self, items): self._items = items
                def all(self): return self._items
            return S(self._items)

    db.execute = AsyncMock(return_value=MockResult([]))
    
    async def mock_scalars(stmt):
        stmt_str = str(stmt).lower()
        if "workspace_members" in stmt_str or "workspacemember" in stmt_str:
            return [make_member("admin")]
        return []

    db.scalars = AsyncMock(side_effect=mock_scalars)
    
    return db


# ── PRD-ADD-01: Master switch tests ────────────────────────────────────────────

@pytest.mark.asyncio
class TestAttendanceEnabledMasterSwitch:

    async def test_f1_disabled_when_attendance_false(self):
        """PRD-ADD-01: F1 must not fire when attendance_enabled=False."""
        ws = make_workspace(attendance_enabled=False)
        member = make_member("member")
        db = make_db()

        result = await check_work_start_for_workspace(db, ws, [member])

        assert result == []
        db.add.assert_not_called()

    async def test_f2_disabled_when_attendance_false(self):
        """PRD-ADD-01: F2 shortfall must not fire when attendance_enabled=False."""
        ws = make_workspace(attendance_enabled=False, daily_required_hours=8.0)
        member = make_member("member")
        db = make_db()

        result = await check_daily_shortfall_for_workspace(
            db, ws, [member], date(2026, 6, 20)
        )

        assert result == []
        db.add.assert_not_called()

    async def test_f1_disabled_when_no_work_start_time(self):
        """PRD-ADD-02: F1 skipped when work_start_time is None (independently nullable)."""
        ws = make_workspace(attendance_enabled=True, work_start_time=None)
        member = make_member("member")
        db = make_db()

        result = await check_work_start_for_workspace(db, ws, [member])

        assert result == []

    async def test_f2_disabled_when_no_daily_hours(self):
        """PRD-ADD-02: F2 skipped when daily_required_hours is None (independently nullable)."""
        ws = make_workspace(attendance_enabled=True, daily_required_hours=None)
        member = make_member("member")
        db = make_db()

        result = await check_daily_shortfall_for_workspace(
            db, ws, [member], date(2026, 6, 20)
        )

        assert result == []


# ── PRD-ADD-03: Member-only scope tests ────────────────────────────────────────

@pytest.mark.asyncio
class TestMemberOnlyScope:

    async def test_f1_skips_admin(self):
        """PRD-ADD-03: Admin role is skipped in F1 evaluation."""
        ws = make_workspace()
        admin = make_member("admin")
        db = make_db()

        with patch(
            "app.services.attendance_service._now_in_tz",
            return_value=datetime(2026, 6, 23, 9, 0, tzinfo=dt_timezone.utc),
        ):
            result = await check_work_start_for_workspace(db, ws, [admin])

        assert result == []

    async def test_f1_skips_manager(self):
        """PRD-ADD-03: Manager role is skipped in F1 evaluation."""
        ws = make_workspace()
        manager = make_member("manager")
        db = make_db()

        with patch(
            "app.services.attendance_service._now_in_tz",
            return_value=datetime(2026, 6, 23, 9, 0, tzinfo=dt_timezone.utc),
        ):
            result = await check_work_start_for_workspace(db, ws, [manager])

        assert result == []

    async def test_f2_skips_admin_as_subject(self):
        """PRD-ADD-03: Admin's own hours are not checked in F2."""
        ws = make_workspace(daily_required_hours=8.0)
        admin = make_member("admin")
        member = make_member("member")
        # admin and manager are recipients; admin is also in members list as subject
        db = make_db()
        db.scalar = AsyncMock(return_value=0)  # zero hours for member

        with patch(
            "app.services.attendance_service._get_hours_logged_today",
            return_value=0.0,
        ):
            result = await check_daily_shortfall_for_workspace(
                db, ws, [admin, member], date(2026, 6, 20)
            )

        # Only member should generate shortfall; admin as subject is skipped
        subject_ids = {n.user_id for n in result}
        assert admin.user_id not in subject_ids


# ── PRD-ADD-04: Off-days suspension ───────────────────────────────────────────

@pytest.mark.asyncio
class TestOffDaysSuspension:

    async def test_f1_suspended_on_off_day(self):
        """PRD-ADD-04: F1 does not fire on workspace off_days."""
        ws = make_workspace(off_days=[1])  # Monday off
        member = make_member("member")
        db = make_db()

        # Patch _is_off_day to return True (off day), and _now_in_tz to return
        # 09:00 (trigger time) — this proves off_day check wins over time match
        monday = datetime(2026, 6, 23, 9, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=monday), \
             patch("app.services.attendance_service._is_off_day", return_value=True):
            result = await check_work_start_for_workspace(db, ws, [member])

        assert result == []

    async def test_f1_fires_on_working_day(self):
        """F1 does fire on non-off days when conditions are met (no existing entries)."""
        # Sunday=0 in Addendum; off_days=[0] means Sunday off, not Monday
        ws = make_workspace(off_days=[0], work_start_time=time(9, 0))
        member = make_member("member")
        db = make_db()

        # Tuesday June 24, 2026 — weekday()=1 → addendum day=2 (not in off_days=[0])
        tuesday = datetime(2026, 6, 24, 9, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=tuesday), \
             patch("app.services.attendance_service._has_any_time_entry_today", return_value=False), \
             patch("app.services.attendance_service._already_notified_today", return_value=False):
            result = await check_work_start_for_workspace(db, ws, [member])

        assert member.user_id in result

    async def test_f2_suspended_on_off_day(self):
        """PRD-ADD-04: F2 does not evaluate shortfall on off_days."""
        # June 22, 2026 = Sunday; Addendum day 0 (Sunday)
        ws = make_workspace(off_days=[0])  # Sunday off
        sunday = date(2026, 6, 22)
        member = make_member("member")
        db = make_db()

        result = await check_daily_shortfall_for_workspace(db, ws, [member], sunday)

        assert result == []


# ── PRD-ADD-08: Flexible Hours suppression ─────────────────────────────────────

@pytest.mark.asyncio
class TestFlexibleHoursSuppression:

    async def test_flexible_reminder_suppressed_when_hours_logged(self):
        """PRD-ADD-08: Flexible Hours reminder MUST NOT fire if member logged any time."""
        ws = make_workspace(attendance_mode="flexible_hours", off_days=[0])
        member = make_member("member")
        db = make_db()

        tuesday = datetime(2026, 6, 24, 9, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=tuesday), \
             patch("app.services.attendance_service._get_hours_logged_today", return_value=0.5), \
             patch("app.services.attendance_service._already_notified_today", return_value=False):
            result = await check_work_start_for_workspace(db, ws, [member])

        # Any hours > 0 must suppress the prompt
        assert result == []

    async def test_flexible_reminder_fires_at_zero_hours(self):
        """PRD-ADD-08: Flexible Hours reminder fires when member has zero hours."""
        ws = make_workspace(attendance_mode="flexible_hours", off_days=[0])
        member = make_member("member")
        db = make_db()

        tuesday = datetime(2026, 6, 24, 9, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=tuesday), \
             patch("app.services.attendance_service._get_hours_logged_today", return_value=0.0), \
             patch("app.services.attendance_service._already_notified_today", return_value=False):
            result = await check_work_start_for_workspace(db, ws, [member])

        assert member.user_id in result


# ── Option B: Pacing formula ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestOptionBPacingFormula:

    async def test_on_pace_when_target_not_set(self):
        """Option B: on_pace=True when daily_required_hours is None (no badge)."""
        ws = make_workspace(attendance_enabled=True, daily_required_hours=None)
        db = make_db()
        db.scalar = AsyncMock(return_value=0)

        result = await get_daily_progress(db, ws, uuid.uuid4())

        assert result["on_pace"] is True
        assert result["daily_required_hours"] is None

    async def test_on_pace_when_attendance_disabled(self):
        """Option B: on_pace=True and daily_required_hours=None when attendance off."""
        ws = make_workspace(attendance_enabled=False, daily_required_hours=8.0)
        db = make_db()

        result = await get_daily_progress(db, ws, uuid.uuid4())

        assert result["on_pace"] is True
        assert result["daily_required_hours"] is None

    async def test_on_pace_true_when_achievable(self):
        """Option B: on_pace=True when enough time remains to hit target."""
        ws = make_workspace(attendance_enabled=True, daily_required_hours=8.0)
        db = make_db()
        user_id = uuid.uuid4()

        # 6 hours logged, 2 hours needed, 3 hours until midnight → achievable
        now_9pm = datetime(2026, 6, 24, 21, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._get_hours_logged_today", return_value=6.0), \
             patch("app.services.attendance_service._now_in_tz", return_value=now_9pm), \
             patch("app.services.attendance_service._today_in_tz", return_value=date(2026, 6, 24)):
            result = await get_daily_progress(db, ws, user_id)

        assert result["on_pace"] is True
        assert result["hours_logged_today"] == 6.0

    async def test_on_pace_false_when_impossible(self):
        """Option B: on_pace=False when mathematically impossible to hit target."""
        ws = make_workspace(attendance_enabled=True, daily_required_hours=8.0)
        db = make_db()
        user_id = uuid.uuid4()

        # 0 hours logged, 8 hours needed, 1 minute until midnight → impossible
        now_1min_to_midnight = datetime(2026, 6, 24, 23, 59, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._get_hours_logged_today", return_value=0.0), \
             patch("app.services.attendance_service._now_in_tz", return_value=now_1min_to_midnight), \
             patch("app.services.attendance_service._today_in_tz", return_value=date(2026, 6, 24)):
            result = await get_daily_progress(db, ws, user_id)

        assert result["on_pace"] is False

    async def test_on_pace_true_when_target_already_met(self):
        """Option B: on_pace=True when member already hit their target."""
        ws = make_workspace(attendance_enabled=True, daily_required_hours=8.0)
        db = make_db()
        user_id = uuid.uuid4()

        now_3pm = datetime(2026, 6, 24, 15, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._get_hours_logged_today", return_value=8.5), \
             patch("app.services.attendance_service._now_in_tz", return_value=now_3pm), \
             patch("app.services.attendance_service._today_in_tz", return_value=date(2026, 6, 24)):
            result = await get_daily_progress(db, ws, user_id)

        assert result["on_pace"] is True


# ── record_work_start_response tests ──────────────────────────────────────────

@pytest.mark.asyncio
class TestRecordWorkStartResponse:

    async def test_not_now_creates_notification(self):
        """'not_now' response creates an AttendanceNotification record."""
        ws = make_workspace(attendance_mode="fixed_schedule", off_days=[0])
        db = make_db()
        user_id = uuid.uuid4()

        now = datetime(2026, 6, 24, 9, 30, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=now):
            result = await record_work_start_response(
                db=db,
                workspace=ws,
                user_id=user_id,
                response="not_now",
                project_id=None,
                task_id=None,
            )

        assert result["acknowledged"] is True
        assert result["time_entry_id"] is None
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert isinstance(added, AttendanceNotification)
        assert added.notification_type == "work_start_missed"

    async def test_not_now_computes_late_minutes_fixed_schedule(self):
        """'not_now' in fixed_schedule mode sets late_by_minutes correctly."""
        ws = make_workspace(
            attendance_mode="fixed_schedule",
            work_start_time=time(9, 0),
            off_days=[0],
        )
        db = make_db()
        user_id = uuid.uuid4()

        # 30 minutes after work_start_time
        now = datetime(2026, 6, 24, 9, 30, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=now):
            await record_work_start_response(
                db=db, workspace=ws, user_id=user_id,
                response="not_now", project_id=None, task_id=None,
            )

        added = db.add.call_args[0][0]
        assert added.late_by_minutes == 30

    async def test_not_now_no_late_minutes_flexible_mode(self):
        """'not_now' in flexible_hours mode: late_by_minutes is always None."""
        ws = make_workspace(
            attendance_mode="flexible_hours",
            work_start_time=time(9, 0),
            off_days=[0],
        )
        db = make_db()
        user_id = uuid.uuid4()

        now = datetime(2026, 6, 24, 9, 30, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=now):
            await record_work_start_response(
                db=db, workspace=ws, user_id=user_id,
                response="not_now", project_id=None, task_id=None,
            )

        added = db.add.call_args[0][0]
        assert added.late_by_minutes is None  # No lateness concept in flexible mode

    async def test_start_response_returns_acknowledged(self):
        """'start' response returns acknowledged=True (timer creation in router)."""
        ws = make_workspace()
        db = make_db()
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()

        now = datetime(2026, 6, 24, 9, 0, tzinfo=dt_timezone.utc)
        with patch("app.services.attendance_service._now_in_tz", return_value=now):
            result = await record_work_start_response(
                db=db, workspace=ws, user_id=user_id,
                response="start", project_id=project_id, task_id=None,
            )

        assert result["acknowledged"] is True
        # Service creates dummy notification so cron skips it
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.notification_type == "work_start_missed"


# ── Settings update tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestUpdateSettings:

    async def test_update_attendance_settings_patches_fields(self):
        """update_attendance_settings only mutates provided fields."""
        ws = make_workspace()
        ws.attendance_enabled = False
        db = make_db()

        await update_attendance_settings(
            db=db,
            workspace=ws,
            attendance_enabled=True,
            attendance_mode=None,
            work_start_time="09:30",
            daily_required_hours=None,
            off_days=None,
        )

        assert ws.attendance_enabled is True
        assert ws.work_start_time == time(9, 30)
        # Unchanged fields stay as-is
        assert ws.daily_required_hours == 8.0

    async def test_update_billable_settings(self):
        """update_billable_settings sets is_billable correctly."""
        ws = make_workspace(is_billable=True)
        db = make_db()

        await update_billable_settings(db=db, workspace=ws, is_billable=False)

        assert ws.is_billable is False

    async def test_billable_re_enable(self):
        """Toggling is_billable back to True restores billable state."""
        ws = make_workspace(is_billable=False)
        db = make_db()

        await update_billable_settings(db=db, workspace=ws, is_billable=True)

        assert ws.is_billable is True
