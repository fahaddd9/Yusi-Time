"""
Unit tests for workspace_service — Phase 2.

Tests use mocked SQLAlchemy sessions. All DB calls are verified via
MagicMock return values, not real DB connections.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceDetail, WorkspaceDetailViewer, WorkspaceUpdate


def make_workspace(**kwargs) -> MagicMock:
    ws = MagicMock(spec=Workspace)
    ws.id = kwargs.get("id", uuid.uuid4())
    ws.name = kwargs.get("name", "Test Workspace")
    ws.logo_url = kwargs.get("logo_url", None)
    ws.default_timezone = kwargs.get("default_timezone", "UTC")
    ws.date_format = kwargs.get("date_format", "MM/DD/YYYY")
    ws.currency = kwargs.get("currency", "USD")
    ws.default_hourly_rate_cents = kwargs.get("default_hourly_rate_cents", None)
    ws.rounding_mode = kwargs.get("rounding_mode", "none")
    ws.rounding_interval_minutes = kwargs.get("rounding_interval_minutes", None)
    ws.mandatory_description = kwargs.get("mandatory_description", False)
    ws.max_timer_duration_seconds = kwargs.get("max_timer_duration_seconds", 86400)
    ws.past_entry_limit_days = kwargs.get("past_entry_limit_days", 30)
    ws.lock_period_days = kwargs.get("lock_period_days", 0)
    ws.approval_workflow_enabled = kwargs.get("approval_workflow_enabled", False)
    ws.idle_detection_enabled = kwargs.get("idle_detection_enabled", False)
    ws.idle_timeout_minutes = kwargs.get("idle_timeout_minutes", None)
    ws.attendance_enabled = kwargs.get("attendance_enabled", False)
    ws.attendance_mode = kwargs.get("attendance_mode", "fixed_schedule")
    ws.work_start_time = kwargs.get("work_start_time", None)
    ws.daily_required_hours = kwargs.get("daily_required_hours", None)
    ws.off_days = kwargs.get("off_days", [0, 6])
    ws.is_billable = kwargs.get("is_billable", True)
    ws.deleted_at = kwargs.get("deleted_at", None)
    ws.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    ws.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))
    return ws


@pytest.mark.asyncio
class TestGetWorkspace:
    async def test_returns_detail_for_admin(self):
        """Admin role → WorkspaceDetail (includes financial fields)."""
        from app.services.workspace_service import get_workspace

        ws = make_workspace(currency="USD", default_hourly_rate_cents=10000)
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=ws)

        result = await get_workspace(mock_db, ws.id, caller_role="admin")
        assert isinstance(result, WorkspaceDetail)

    async def test_returns_detail_for_member(self):
        """Member role → WorkspaceDetail (includes financial fields)."""
        from app.services.workspace_service import get_workspace

        ws = make_workspace()
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=ws)

        result = await get_workspace(mock_db, ws.id, caller_role="member")
        assert isinstance(result, WorkspaceDetail)

    async def test_returns_viewer_schema_for_viewer(self):
        """Viewer role → WorkspaceDetailViewer (financial fields absent)."""
        from app.services.workspace_service import get_workspace

        ws = make_workspace()
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=ws)

        result = await get_workspace(mock_db, ws.id, caller_role="viewer")
        assert isinstance(result, WorkspaceDetailViewer)
        # Financial fields must not be present in the output dict
        result_dict = result.model_dump()
        assert "currency" not in result_dict
        assert "default_hourly_rate_cents" not in result_dict

    async def test_raises_404_for_soft_deleted_workspace(self):
        """Soft-deleted workspace (deleted_at set) → 404 NOT_FOUND."""
        from app.services.workspace_service import get_workspace

        ws = make_workspace(deleted_at=datetime.now(timezone.utc))
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=ws)

        with pytest.raises(HTTPException) as exc:
            await get_workspace(mock_db, ws.id, caller_role="admin")
        assert exc.value.status_code == 404

    async def test_raises_404_when_workspace_not_found(self):
        """Non-existent workspace → 404 NOT_FOUND."""
        from app.services.workspace_service import get_workspace

        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await get_workspace(mock_db, uuid.uuid4(), caller_role="admin")
        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestUpdateWorkspace:
    async def test_applies_patch_fields_only(self):
        """Only provided fields are updated (PATCH semantics)."""
        from app.services.workspace_service import update_workspace

        ws = make_workspace(name="Old Name")
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=ws)

        data = WorkspaceUpdate(name="New Name")
        await update_workspace(mock_db, ws.id, data)

        assert ws.name == "New Name"

    async def test_raises_404_for_deleted_workspace(self):
        """Cannot update soft-deleted workspace → 404."""
        from app.services.workspace_service import update_workspace

        ws = make_workspace(deleted_at=datetime.now(timezone.utc))
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=ws)

        data = WorkspaceUpdate(name="New Name")
        with pytest.raises(HTTPException) as exc:
            await update_workspace(mock_db, ws.id, data)
        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestWorkspaceUpdateSchemaValidation:
    def test_rounding_mode_requires_interval(self):
        """rounding_mode != 'none' without interval → ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            WorkspaceUpdate(rounding_mode="nearest")

    def test_rounding_mode_none_does_not_require_interval(self):
        """rounding_mode='none' without interval → valid."""
        update = WorkspaceUpdate(rounding_mode="none")
        assert update.rounding_mode == "none"
        assert update.rounding_interval_minutes is None

    def test_rounding_mode_nearest_with_interval_valid(self):
        """rounding_mode='nearest' + interval → valid."""
        update = WorkspaceUpdate(rounding_mode="nearest", rounding_interval_minutes=15)
        assert update.rounding_mode == "nearest"
        assert update.rounding_interval_minutes == 15

    def test_idle_enabled_requires_timeout(self):
        """idle_detection_enabled=True without timeout → ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            WorkspaceUpdate(idle_detection_enabled=True)

    def test_idle_enabled_with_timeout_valid(self):
        """idle_detection_enabled=True + timeout → valid."""
        update = WorkspaceUpdate(idle_detection_enabled=True, idle_timeout_minutes=5)
        assert update.idle_detection_enabled is True
        assert update.idle_timeout_minutes == 5
