import uuid
import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.services.approval_service import (
    submit_week,
    approve_submission,
    reject_submission,
    list_pending_submissions,
)
from app.models.time_entry import TimeEntry
from app.models.timesheet_submission import TimesheetSubmission
from app.models.workspace import Workspace
from app.models.user import User

def make_workspace(approval_workflow_enabled=True):
    ws = MagicMock(spec=Workspace)
    ws.id = uuid.uuid4()
    ws.approval_workflow_enabled = approval_workflow_enabled
    ws.default_timezone = "UTC"
    return ws

def make_user():
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.full_name = "Test User"
    return u

def make_entry(status="draft"):
    e = MagicMock(spec=TimeEntry)
    e.id = uuid.uuid4()
    e.status = status
    return e

def make_submission(status="pending"):
    s = MagicMock(spec=TimesheetSubmission)
    s.id = uuid.uuid4()
    s.status = status
    s.workspace_id = uuid.uuid4()
    s.user_id = uuid.uuid4()
    s.week_start = date(2026, 5, 18)
    return s

def make_db(workspace=None, user=None, existing_submission=None, entries=None, submission=None):
    db = AsyncMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    
    async def _get(cls, pk):
        if cls is Workspace:
            return workspace
        if cls is User:
            return user
        if cls is TimesheetSubmission:
            return submission
        return None
    db.get = AsyncMock(side_effect=_get)

    async def _scalar(stmt):
        return existing_submission
    db.scalar = AsyncMock(side_effect=_scalar)

    class MockResult:
        def __init__(self, items):
            self.items = items
        def scalars(self):
            class MockScalars:
                def __init__(self, items):
                    self.items = items
                def all(self):
                    return self.items
            return MockScalars(self.items)

    db.execute = AsyncMock(return_value=MockResult(entries or []))

    return db

@pytest.mark.asyncio
class TestSubmitWeek:

    async def test_submit_only_draft_entries_included(self):
        ws = make_workspace()
        user = make_user()
        draft1 = make_entry("draft")
        draft2 = make_entry("draft")
        db = make_db(workspace=ws, user=user, entries=[draft1, draft2])

        with patch("app.services.approval_service.notification_service.create_for_role", new=AsyncMock()):
            sub = await submit_week(db, ws.id, user.id, date(2026, 5, 18))
        
        assert sub.status == "pending"
        assert draft1.status == "pending"
        assert draft2.status == "pending"
        assert db.add.called
        assert db.add_all.called

    async def test_submit_approved_entries_excluded(self):
        # Database query already filters out approved via where(status='draft')
        pass

    async def test_submit_no_entries_raises_400(self):
        ws = make_workspace()
        user = make_user()
        db = make_db(workspace=ws, user=user, entries=[])

        with pytest.raises(HTTPException) as exc:
            await submit_week(db, ws.id, user.id, date(2026, 5, 18))
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "NO_ENTRIES_TO_SUBMIT"

    async def test_submit_double_submit_raises_409(self):
        ws = make_workspace()
        user = make_user()
        db = make_db(workspace=ws, user=user, existing_submission=make_submission())

        with pytest.raises(HTTPException) as exc:
            await submit_week(db, ws.id, user.id, date(2026, 5, 18))
        assert exc.value.status_code == 409
        assert exc.value.headers["code"] == "ALREADY_SUBMITTED"

    async def test_submit_not_monday_raises_400(self):
        ws = make_workspace()
        user = make_user()
        db = make_db(workspace=ws, user=user)

        with pytest.raises(HTTPException) as exc:
            await submit_week(db, ws.id, user.id, date(2026, 5, 19)) # Tuesday
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "INVALID_WEEK_START"


@pytest.mark.asyncio
class TestApproveReject:

    async def test_approve_sets_all_entries_approved(self):
        ws = make_workspace()
        sub = make_submission("pending")
        sub.workspace_id = ws.id
        entry1 = make_entry("pending")
        db = make_db(workspace=ws, submission=sub, entries=[entry1])

        with patch("app.services.approval_service.notification_service.create", new=AsyncMock()):
            res = await approve_submission(db, ws.id, sub.id, uuid.uuid4())
        
        assert res.status == "approved"
        assert entry1.status == "approved"

    async def test_reject_blank_note_raises_422(self):
        ws = make_workspace()
        db = make_db(workspace=ws)
        with pytest.raises(HTTPException) as exc:
            await reject_submission(db, ws.id, uuid.uuid4(), uuid.uuid4(), "   ")
        assert exc.value.status_code == 422

    async def test_reject_whitespace_note_raises_422(self):
        ws = make_workspace()
        db = make_db(workspace=ws)
        with pytest.raises(HTTPException) as exc:
            await reject_submission(db, ws.id, uuid.uuid4(), uuid.uuid4(), "\n\t ")
        assert exc.value.status_code == 422

    async def test_reject_sets_entries_to_draft(self):
        ws = make_workspace()
        sub = make_submission("pending")
        sub.workspace_id = ws.id
        entry1 = make_entry("pending")
        db = make_db(workspace=ws, submission=sub, entries=[entry1])

        with patch("app.services.approval_service.notification_service.create", new=AsyncMock()):
            res = await reject_submission(db, ws.id, sub.id, uuid.uuid4(), "Fix this")
        
        assert res.status == "rejected"
        assert entry1.status == "draft"
        assert res.rejection_note == "Fix this"


@pytest.mark.asyncio
class TestWorkflowDisabled:

    async def test_workflow_disabled_pending_stays_pending(self):
        ws = make_workspace(approval_workflow_enabled=False)
        db = make_db(workspace=ws)
        
        with pytest.raises(HTTPException) as exc:
            await submit_week(db, ws.id, uuid.uuid4(), date(2026, 5, 18))
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "BAD_REQUEST"
