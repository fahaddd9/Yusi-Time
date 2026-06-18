import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.models.time_entry import TimeEntry
from app.models.time_entry_tag import TimeEntryTag
from app.services.time_entry_service import continue_entry, duplicate_entry

from tests.unit.test_time_entry_service import make_db, make_workspace, make_project, make_user, make_entry, make_task

@pytest.mark.asyncio
class TestContinueEntry:

    async def _make_db_for_continue(self, source, running_entry, workspace, project, user, tag_id=None):
        db = AsyncMock()
        added_entries = []
        db.add = MagicMock(side_effect=lambda obj: added_entries.append(obj))
        db.flush = AsyncMock()
        
        async def _get(cls, pk):
            from app.models.workspace import Workspace
            from app.models.project import Project
            from app.models.user import User
            from app.models.task import Task
            if cls is Workspace: return workspace
            if cls is Project: return project
            if cls is User: return user
            if cls is Task: return None
            return None
        db.get = _get

        # mock for _load_entry_with_tags and _get_running_timer
        # _load_entry_with_tags needs source with .tags
        mock_source = source
        if mock_source:
            # We add a tags property if needed
            if tag_id:
                mock_tag = MagicMock()
                mock_tag.tag_id = tag_id
                mock_source.tags = [mock_tag]
            else:
                mock_source.tags = []
        
        mock_scalar = MagicMock()
        
        # We can implement a side effect for execute
        async def _execute(stmt):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "status = 'running'" in stmt_str or "status = :status_1" in stmt_str:
                 res.scalar_one_or_none = MagicMock(return_value=running_entry)
            else:
                 # Check if we are loading the newly added entry
                 # by looking at added_entries
                 from app.models.time_entry import TimeEntry
                 entries = [e for e in added_entries if isinstance(e, TimeEntry)]
                 if entries:
                     entries[-1].tags = [] # Provide empty tags for mock
                     res.scalar_one_or_none = MagicMock(return_value=entries[-1])
                 else:
                     res.scalar_one_or_none = MagicMock(return_value=mock_source)
            return res
            
        db.execute = AsyncMock(side_effect=_execute)
        
        return db

    async def test_continue_draft_entry_creates_running(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        db = await self._make_db_for_continue(source, None, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            entry, ret_user, ret_project, ret_task = await continue_entry(
                db=db, user_id=user.id, workspace_id=ws.id,
                caller_role="member", entry_id=str(source.id), force=False
            )
            
        assert entry.status == "running"
        assert entry.hourly_rate_cents == 15000
        assert entry.project_id == project.id
        db.add.assert_called()

    async def test_continue_approved_entry_creates_running(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="approved", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        db = await self._make_db_for_continue(source, None, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            entry, _, _, _ = await continue_entry(
                db=db, user_id=user.id, workspace_id=ws.id,
                caller_role="member", entry_id=str(source.id), force=False
            )
        assert entry.status == "running"

    async def test_continue_pending_raises_400(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="pending", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        db = await self._make_db_for_continue(source, None, ws, project, user)

        with pytest.raises(HTTPException) as exc:
            await continue_entry(db, user.id, ws.id, "member", str(source.id), False)
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "CANNOT_CONTINUE_PENDING"

    async def test_continue_other_user_member_raises_403(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        other_user_id = uuid.uuid4()
        source = make_entry(status="draft", workspace_id=ws.id, user_id=other_user_id, project_id=project.id)
        db = await self._make_db_for_continue(source, None, ws, project, user)

        with pytest.raises(HTTPException) as exc:
            await continue_entry(db, user.id, ws.id, "member", str(source.id), False)
        assert exc.value.status_code == 403
        assert exc.value.headers["code"] == "FORBIDDEN"

    async def test_continue_force_true_stops_running_first(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        running = make_entry(status="running", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        db = await self._make_db_for_continue(source, running, ws, project, user)

        with pytest.raises(HTTPException) as exc:
            await continue_entry(db, user.id, ws.id, "member", str(source.id), False)
        assert exc.value.status_code == 409

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            with patch("app.services.time_entry_service.stop_timer", new=AsyncMock()) as mock_stop:
                await continue_entry(db, user.id, ws.id, "member", str(source.id), True)
                mock_stop.assert_called_once()

    async def test_continue_fresh_rate_not_source_rate(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id, hourly_rate_cents=5000)
        db = await self._make_db_for_continue(source, None, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=20000)):
            entry, _, _, _ = await continue_entry(db, user.id, ws.id, "member", str(source.id), False)
        assert entry.hourly_rate_cents == 20000

    async def test_continue_copies_all_tags(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        db = await self._make_db_for_continue(source, None, ws, project, user, tag_id=uuid.uuid4())

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            entry, _, _, _ = await continue_entry(db, user.id, ws.id, "member", str(source.id), False)
            
        # Verify db.add was called with a TimeEntryTag
        added_objects = [call[0][0] for call in db.add.call_args_list]
        tag_added = any(isinstance(obj, TimeEntryTag) for obj in added_objects)
        assert tag_added


@pytest.mark.asyncio
class TestDuplicateEntry:

    async def _make_db_for_duplicate(self, source, workspace, project, user, tag_id=None):
        db = AsyncMock()
        added_entries = []
        db.add = MagicMock(side_effect=lambda obj: added_entries.append(obj))
        db.flush = AsyncMock()
        
        async def _get(cls, pk):
            from app.models.workspace import Workspace
            from app.models.project import Project
            from app.models.user import User
            from app.models.task import Task
            if cls is Workspace: return workspace
            if cls is Project: return project
            if cls is User: return user
            if cls is Task: return None
            return None
        db.get = _get

        mock_source = source
        if mock_source:
            if tag_id:
                mock_tag = MagicMock()
                mock_tag.tag_id = tag_id
                mock_source.tags = [mock_tag]
            else:
                mock_source.tags = []
        
        async def _execute(stmt):
            res = MagicMock()
            from app.models.time_entry import TimeEntry
            entries = [e for e in added_entries if isinstance(e, TimeEntry)]
            if entries:
                entries[-1].tags = []
                res.scalar_one_or_none = MagicMock(return_value=entries[-1])
            else:
                res.scalar_one_or_none = MagicMock(return_value=mock_source)
            return res
            
        db.execute = AsyncMock(side_effect=_execute)
        return db

    async def test_duplicate_pending_raises_400(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        source = make_entry(status="pending", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        db = await self._make_db_for_duplicate(source, ws, project, user)

        with pytest.raises(HTTPException) as exc:
            await duplicate_entry(db, user.id, ws.id, "member", str(source.id))
        assert exc.value.status_code == 400

    async def test_duplicate_start_time_today_midnight_utc(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        source.duration_seconds = 3600
        db = await self._make_db_for_duplicate(source, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            entry, _, _, _, _ = await duplicate_entry(db, user.id, ws.id, "member", str(source.id))
            
        now = datetime.now(timezone.utc)
        expected_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        assert entry.start_time == expected_start
        assert entry.end_time == expected_start + timedelta(seconds=3600)

    async def test_duplicate_applies_rounding_and_returns_result(self):
        ws = make_workspace(rounding_mode="up", rounding_interval_minutes=15)
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        source.duration_seconds = 3780 # 63 minutes
        db = await self._make_db_for_duplicate(source, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            entry, _, _, _, rounding = await duplicate_entry(db, user.id, ws.id, "member", str(source.id))
            
        assert rounding.raw_seconds == 3780
        assert rounding.rounded_seconds == 4500 # UP to 75 minutes
        assert entry.duration_seconds == 4500
        
    async def test_duplicate_computes_billable_amount(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        source.duration_seconds = 3600 # 1 hour
        db = await self._make_db_for_duplicate(source, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)): # $150.00
            entry, _, _, _, _ = await duplicate_entry(db, user.id, ws.id, "member", str(source.id))
            
        assert entry.billable_amount_cents == 15000

    async def test_duplicate_source_entry_unchanged(self):
        ws = make_workspace()
        project = make_project(workspace_id=ws.id)
        user = make_user()
        
        old_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        source = make_entry(status="draft", workspace_id=ws.id, user_id=user.id, project_id=project.id)
        source.start_time = old_start
        source.duration_seconds = 3600
        db = await self._make_db_for_duplicate(source, ws, project, user)

        with patch("app.services.time_entry_service.rate_service.resolve_rate", new=AsyncMock(return_value=15000)):
            entry, _, _, _, _ = await duplicate_entry(db, user.id, ws.id, "member", str(source.id))
            
        assert source.start_time == old_start
        assert entry.id != source.id
