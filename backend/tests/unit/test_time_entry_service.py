"""
Time Entry Service — Unit Tests
Implementation Plan §4.7 — Backend Testing Checklist.

All tests use mock AsyncSession (no live DB required).
Tests cover the service layer only — router is tested via integration tests.

Checklist coverage:
  [x] start_timer: mandatory description missing → 400
  [x] start_timer: force=false, timer running → 409 TIMER_ALREADY_RUNNING
  [x] stop_timer: not running → 400
  [x] stop_timer: duration = ROUNDED (never raw)
  [x] stop_timer: rounding result always returned
  [x] stop_timer: idle_end_time → duration = idle_end - start
  [x] create_manual_entry: past limit → 400 PAST_ENTRY_LIMIT_EXCEEDED
  [x] create_manual_entry: overlap → has_overlap=true, entry created
  [x] update_entry: pending → 403 ENTRY_LOCKED
  [x] update_entry: approved admin → 200 (not locked)
  [x] update_entry: rounding re-applied from new raw value
  [x] update_entry: rate re-snapshotted from current hierarchy
  [x] delete_entry: pending → 403 ENTRY_LOCKED
  [x] Viewer financial isolation — tested in test_rate_service.py + schema layer
  [x] Rounding all modes — tested in test_rounding_service.py (28 tests)
  [x] Rate hierarchy — tested in test_rate_service.py (10 tests)
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call
from fastapi import HTTPException


# ─── Shared mock builders ─────────────────────────────────────────────────────

def make_workspace(
    rounding_mode="none",
    rounding_interval_minutes=None,
    mandatory_description=False,
    past_entry_limit_days=7,
    lock_period_days=7,
    max_timer_duration_seconds=86400,
):
    ws = MagicMock()
    ws.id = uuid.uuid4()
    ws.rounding_mode = rounding_mode
    ws.rounding_interval_minutes = rounding_interval_minutes
    ws.mandatory_description = mandatory_description
    ws.past_entry_limit_days = past_entry_limit_days
    ws.lock_period_days = lock_period_days
    ws.max_timer_duration_seconds = max_timer_duration_seconds
    ws.default_hourly_rate_cents = None
    return ws


def make_project(workspace_id=None, default_billable=True, visibility="public", status="active", rate_cents=None, color=None):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.workspace_id = workspace_id or uuid.uuid4()
    p.name = "Test Project"
    p.default_billable = default_billable
    p.visibility = visibility
    p.status = status
    p.hourly_rate_cents = rate_cents
    p.color = color
    p.client_id = None
    return p


def make_task(project_id=None, rate_cents=None):
    t = MagicMock()
    t.id = uuid.uuid4()
    t.project_id = project_id or uuid.uuid4()
    t.name = "Test Task"
    t.hourly_rate_cents = rate_cents
    return t


def make_entry(
    workspace_id=None,
    user_id=None,
    status="draft",
    start_time=None,
    end_time=None,
    duration_seconds=None,
    task_id=None,
    project_id=None,
    hourly_rate_cents=None,
    billable_amount_cents=None,
):
    e = MagicMock()
    e.id = uuid.uuid4()
    e.workspace_id = workspace_id or uuid.uuid4()
    e.user_id = user_id or uuid.uuid4()
    e.project_id = project_id or uuid.uuid4()
    e.task_id = task_id
    e.status = status
    e.start_time = start_time or datetime.now(timezone.utc) - timedelta(hours=1)
    e.end_time = end_time
    e.duration_seconds = duration_seconds
    e.description = None
    e.billable = True
    e.hourly_rate_cents = hourly_rate_cents
    e.billable_amount_cents = billable_amount_cents
    e.tags = []
    e.created_at = datetime.now(timezone.utc)
    e.updated_at = datetime.now(timezone.utc)
    return e


def make_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.full_name = "Test User"
    u.is_active = True
    return u


def make_db(workspace=None, project=None, task=None, entry=None, user=None, running_entry=None):
    """
    Build a mock AsyncSession that dispatches .get() and .execute() by type/context.
    """
    from app.models.workspace import Workspace
    from app.models.project import Project
    from app.models.task import Task
    from app.models.time_entry import TimeEntry
    from app.models.user import User

    db = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()

    async def _get(model_class, pk):
        if model_class is Workspace:
            return workspace
        if model_class is Project:
            return project
        if model_class is Task:
            return task
        if model_class is TimeEntry:
            return entry
        if model_class is User:
            return user
        return None

    db.get = _get

    # execute() is used by _get_running_timer and _load_entry_with_tags
    mock_scalar = AsyncMock()
    mock_scalar.scalar_one_or_none = MagicMock(return_value=running_entry)
    mock_scalar.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=mock_scalar)

    return db


# ─── start_timer tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestStartTimer:

    async def test_mandatory_description_missing_raises_400(self):
        ws = make_workspace(mandatory_description=True)
        project = make_project(workspace_id=ws.id)
        db = make_db(workspace=ws, project=project)

        from app.services.time_entry_service import start_timer
        with pytest.raises(HTTPException) as exc:
            await start_timer(
                db=db, user_id=uuid.uuid4(), workspace_id=ws.id,
                caller_role="member", project_id=project.id,
                task_id=None, description=None, tag_ids=[],
                billable=None, force=False,
            )
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "MANDATORY_DESCRIPTION"

    async def test_timer_already_running_force_false_raises_409(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        running = make_entry(status="running")
        db = make_db(workspace=ws, project=project, running_entry=running)

        from app.services.time_entry_service import start_timer
        with pytest.raises(HTTPException) as exc:
            await start_timer(
                db=db, user_id=uuid.uuid4(), workspace_id=ws.id,
                caller_role="member", project_id=project.id,
                task_id=None, description="work", tag_ids=[],
                billable=None, force=False,
            )
        assert exc.value.status_code == 409
        assert exc.value.headers["code"] == "TIMER_ALREADY_RUNNING"

    async def test_billable_defaults_to_project_default(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id, default_billable=False)
        user = make_user()
        db = make_db(workspace=ws, project=project, user=user)

        # Intercept the TimeEntry that gets added
        added_entries = []
        db.add = MagicMock(side_effect=lambda obj: added_entries.append(obj))
        
        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none = MagicMock(side_effect=lambda: added_entries[0] if added_entries else None)
        db.execute = AsyncMock(return_value=mock_scalar)

        from app.services.time_entry_service import start_timer
        from app.models.time_entry import TimeEntry as TE

        # Patch rate_service.resolve_rate so it doesn't need a real DB
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
            entry, ret_user, ret_project, ret_task = await start_timer(
                db=db, user_id=user.id, workspace_id=ws.id,
                caller_role="member", project_id=project.id,
                task_id=None, description=None, tag_ids=[],
                billable=None, force=False,
            )
        # The returned entry is the real TimeEntry object created inside the service
        assert entry.billable == False  # inherited from project.default_billable=False


# ─── stop_timer tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestStopTimer:

    async def _run_stop(self, entry, workspace, user, rounding_mode="up", rounding_interval=15):
        """Helper to run stop_timer with a given workspace rounding config."""
        ws = workspace
        ws.rounding_mode = rounding_mode
        ws.rounding_interval_minutes = rounding_interval

        from app.models.project import Project
        from app.models.task import Task
        from app.models.user import User
        from app.models.workspace import Workspace
        from app.models.time_entry import TimeEntry

        db = AsyncMock()
        db.add = MagicMock()

        async def _get(model_class, pk):
            if model_class is Workspace:
                return ws
            if model_class is Project:
                return make_project()
            if model_class is Task:
                return None
            if model_class is User:
                return user
            return None

        db.get = _get

        # _load_entry_with_tags uses execute()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=entry)
        db.execute = AsyncMock(return_value=mock_result)

        from app.services.time_entry_service import stop_timer
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=5000)):
            return await stop_timer(
                db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                caller_role="admin", entry_id=str(entry.id), idle_end_time=None,
            )

    async def test_stop_non_running_raises_400(self):
        from app.services.time_entry_service import stop_timer
        entry = make_entry(status="draft")

        from app.models.time_entry import TimeEntry
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=entry)
        db.execute = AsyncMock(return_value=mock_result)

        ws = make_workspace()

        async def _get(cls, pk):
            from app.models.workspace import Workspace
            if cls is Workspace:
                return ws
            return entry

        db.get = _get

        with pytest.raises(HTTPException) as exc:
            with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
                await stop_timer(db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                                 caller_role="admin", entry_id=str(entry.id), idle_end_time=None)
        assert exc.value.status_code == 400

    async def test_stop_stores_rounded_not_raw_duration(self):
        """
        Implementation Plan §4.7 — duration_seconds on stopped entry = ROUNDED.
        Start 1h 3min ago → raw=3780s. UP 15min → rounded=4500s.
        """
        user = make_user()
        start = datetime.now(timezone.utc) - timedelta(seconds=3780)
        entry = make_entry(status="running", start_time=start, user_id=user.id)
        ws = make_workspace(rounding_mode="up", rounding_interval_minutes=15)

        _, _, _, _, rounding = await self._run_stop(entry, ws, user, "up", 15)

        # Service mutates the mock entry object in-place
        assert entry.duration_seconds == 4500  # ROUNDED (not raw 3780)
        assert rounding.raw_seconds == 3780
        assert rounding.rounded_seconds == 4500

    async def test_stop_rounding_result_always_returned(self):
        """Rounding result must always be returned even when mode=none."""
        user = make_user()
        start = datetime.now(timezone.utc) - timedelta(seconds=3780)
        entry = make_entry(status="running", start_time=start, user_id=user.id)
        ws = make_workspace(rounding_mode="none")

        _, _, _, _, rounding = await self._run_stop(entry, ws, user, "none", None)

        assert rounding is not None
        assert rounding.raw_seconds == 3780
        assert rounding.rounded_seconds == 3780  # unchanged for NONE mode

    async def test_stop_idle_end_time_used_for_duration(self):
        """
        When idle_end_time is provided, duration = idle_end_time - start_time.
        Implementation Plan §4.7 — PRD §3.3.3 idle detection.
        """
        user = make_user()
        start = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        idle_end = datetime(2026, 1, 1, 9, 45, 0, tzinfo=timezone.utc)   # 1h45m = 6300s
        entry = make_entry(status="running", start_time=start, user_id=user.id)
        ws = make_workspace(rounding_mode="none")

        from app.models.project import Project
        from app.models.task import Task
        from app.models.user import User
        from app.models.workspace import Workspace

        db = AsyncMock()
        db.add = MagicMock()

        async def _get(model_class, pk):
            if model_class is Workspace:
                return ws
            if model_class is Project:
                return make_project()
            if model_class is User:
                return user
            return None

        db.get = _get
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=entry)
        db.execute = AsyncMock(return_value=mock_result)

        from app.services.time_entry_service import stop_timer
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
            _, _, _, _, rounding = await stop_timer(
                db=db, user_id=user.id, workspace_id=entry.workspace_id,
                caller_role="admin", entry_id=str(entry.id), idle_end_time=idle_end,
            )

        assert rounding.raw_seconds == 6300    # 1h45m = 6300s from idle_end_time
        assert entry.end_time == idle_end      # end_time set to idle_end_time


# ─── create_manual_entry tests ────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCreateManualEntry:

    async def test_past_entry_limit_raises_400(self):
        ws = make_workspace(past_entry_limit_days=7)
        project = make_project(workspace_id=ws.id)
        db = make_db(workspace=ws, project=project)

        start = datetime.now(timezone.utc) - timedelta(days=8)  # 8 days > 7 day limit
        end = start + timedelta(hours=1)

        from app.services.time_entry_service import create_manual_entry
        with pytest.raises(HTTPException) as exc:
            with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
                await create_manual_entry(
                    db=db, user_id=uuid.uuid4(), workspace_id=ws.id,
                    caller_role="member", project_id=project.id, task_id=None,
                    start_time=start, end_time=end,
                    description=None, billable=None, tag_ids=[],
                )
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "PAST_ENTRY_LIMIT_EXCEEDED"

    async def test_overlap_returns_has_overlap_true_but_creates_entry(self):
        """
        When overlapping entries exist, has_overlap=true is returned
        but the entry is STILL created (PRD §5 — overlap is a soft warning).
        """
        ws = make_workspace(past_entry_limit_days=30)
        project = make_project(workspace_id=ws.id)
        user = make_user()

        existing_overlap = make_entry(status="draft")  # simulates overlapping entry
        db = make_db(workspace=ws, project=project, user=user, running_entry=existing_overlap)

        start = datetime.now(timezone.utc) - timedelta(hours=2)
        end = datetime.now(timezone.utc) - timedelta(hours=1)

        added = []
        db.add = MagicMock(side_effect=lambda obj: added.append(obj))

        from app.services.time_entry_service import create_manual_entry
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
            entry, _, _, _, rounding, has_overlap = await create_manual_entry(
                db=db, user_id=user.id, workspace_id=ws.id,
                caller_role="member", project_id=project.id, task_id=None,
                start_time=start, end_time=end,
                description=None, billable=None, tag_ids=[],
            )

        assert has_overlap is True
        assert entry is not None  # entry was created despite overlap

    async def test_start_after_end_raises_400(self):
        ws = make_workspace(past_entry_limit_days=30)
        project = make_project(workspace_id=ws.id)
        db = make_db(workspace=ws, project=project)

        start = datetime.now(timezone.utc)
        end = start - timedelta(minutes=5)  # end BEFORE start

        from app.services.time_entry_service import create_manual_entry
        with pytest.raises(HTTPException) as exc:
            with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
                await create_manual_entry(
                    db=db, user_id=uuid.uuid4(), workspace_id=ws.id,
                    caller_role="member", project_id=project.id, task_id=None,
                    start_time=start, end_time=end,
                    description=None, billable=None, tag_ids=[],
                )
        assert exc.value.status_code == 400


# ─── update_entry / delete_entry lock tests ───────────────────────────────────

@pytest.mark.asyncio
class TestLockRules:

    async def _make_db_for_update(self, entry, workspace):
        from app.models.time_entry import TimeEntry
        db = AsyncMock()
        db.add = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=entry)
        db.execute = AsyncMock(return_value=mock_result)

        async def _get(cls, pk):
            from app.models.workspace import Workspace
            from app.models.project import Project
            from app.models.user import User
            if cls is Workspace:
                return workspace
            if cls is Project:
                return make_project()
            if cls is User:
                return make_user()
            return entry

        db.get = _get
        return db

    async def test_update_pending_entry_non_admin_raises_403_entry_locked(self):
        """Implementation Plan §4.7 — PATCH pending → 403 ENTRY_LOCKED for non-Admin."""
        entry = make_entry(status="pending")
        ws = make_workspace(lock_period_days=7)
        db = await self._make_db_for_update(entry, ws)

        from app.services.time_entry_service import update_entry
        with pytest.raises(HTTPException) as exc:
            with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=None)):
                await update_entry(
                    db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                    caller_role="member", entry_id=str(entry.id),
                    project_id=None, task_id=None, start_time=None, end_time=None,
                    description="new desc", billable=None, tag_ids=None,
                )
        assert exc.value.status_code == 403
        assert exc.value.headers["code"] == "ENTRY_LOCKED"

    async def test_update_approved_entry_admin_succeeds(self):
        """Implementation Plan §4.7 — PATCH approved + admin → 200 (admin bypasses locks)."""
        start = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        entry = make_entry(status="approved", start_time=start, end_time=end, duration_seconds=3600)
        ws = make_workspace(lock_period_days=7)
        db = await self._make_db_for_update(entry, ws)

        from app.services.time_entry_service import update_entry
        # Admin can update approved entries — should NOT raise
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=5000)):
            result = await update_entry(
                db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                caller_role="admin", entry_id=str(entry.id),
                project_id=None, task_id=None, start_time=None, end_time=None,
                description="admin override", billable=None, tag_ids=None,
            )
        assert result is not None  # No exception raised

    async def test_update_re_rounds_from_new_raw_value(self):
        """
        Implementation Plan §4.7 — PATCH re-applies rounding from NEW raw value.
        Entry currently has 3600s. We edit to give 1h3m (3780s) raw, UP 15min → 4500s.
        """
        start = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        entry = make_entry(status="draft", start_time=start, end_time=end, duration_seconds=3600)
        ws = make_workspace(rounding_mode="up", rounding_interval_minutes=15, lock_period_days=0)
        db = await self._make_db_for_update(entry, ws)

        new_end = datetime(2026, 1, 1, 10, 3, 0, tzinfo=timezone.utc)  # +3min → raw 3780s

        from app.services.time_entry_service import update_entry
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=5000)):
            _, _, _, _, rounding = await update_entry(
                db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                caller_role="member", entry_id=str(entry.id),
                project_id=None, task_id=None,
                start_time=None, end_time=new_end,
                description=None, billable=None, tag_ids=None,
            )

        assert rounding.raw_seconds == 3780
        assert rounding.rounded_seconds == 4500  # UP 15min
        assert entry.duration_seconds == 4500    # stored rounded, not raw

    async def test_update_re_snapshots_rate(self):
        """
        Implementation Plan §4.7 — PATCH re-snapshots rate from current hierarchy.
        Even if the original entry had rate_cents=5000, after update it should use the NEW rate.
        """
        start = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        entry = make_entry(status="draft", start_time=start, end_time=end,
                           duration_seconds=3600, hourly_rate_cents=5000)
        ws = make_workspace(lock_period_days=0)
        db = await self._make_db_for_update(entry, ws)

        new_rate = 7500  # rate changed in hierarchy since original entry was created

        from app.services.time_entry_service import update_entry
        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=new_rate)):
            await update_entry(
                db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                caller_role="member", entry_id=str(entry.id),
                project_id=None, task_id=None,
                start_time=None, end_time=None,
                description="updated", billable=None, tag_ids=None,
            )

        assert entry.hourly_rate_cents == 7500  # fresh snapshot, not old 5000

    async def test_delete_pending_entry_non_admin_raises_403(self):
        """Implementation Plan §4.7 — DELETE pending → 403 ENTRY_LOCKED."""
        entry = make_entry(status="pending")
        ws = make_workspace(lock_period_days=7)

        db = AsyncMock()

        async def _get(cls, pk):
            from app.models.workspace import Workspace
            from app.models.time_entry import TimeEntry
            if cls is Workspace:
                return ws
            if cls is TimeEntry:
                return entry
            return None

        db.get = _get

        from app.services.time_entry_service import delete_entry
        with pytest.raises(HTTPException) as exc:
            await delete_entry(
                db=db, user_id=entry.user_id, workspace_id=entry.workspace_id,
                caller_role="member", entry_id=str(entry.id),
            )
        assert exc.value.status_code == 403
        assert exc.value.headers["code"] == "ENTRY_LOCKED"


# ─── _compute_billable_amount helper ─────────────────────────────────────────

def test_compute_billable_none_when_rate_is_none():
    from app.services.time_entry_service import _compute_billable_amount
    assert _compute_billable_amount(3600, None) is None


def test_compute_billable_1h_at_75_dollars():
    from app.services.time_entry_service import _compute_billable_amount
    # 3600s @ 7500 cents/hr = 7500 cents ($75.00)
    assert _compute_billable_amount(3600, 7500) == 7500


def test_compute_billable_30min_at_100_dollars():
    from app.services.time_entry_service import _compute_billable_amount
    # 1800s @ 10000 cents/hr = 5000 cents ($50.00)
    assert _compute_billable_amount(1800, 10000) == 5000
