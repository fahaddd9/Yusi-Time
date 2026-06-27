"""
Attendance Router — Phase 6.5, Addendum §4.1, §4.2, §4.4.

Endpoints:
  PATCH  /workspaces/{id}/attendance-settings  — F1/F2 config (Admin only)
  PATCH  /workspaces/{id}/billable-settings    — is_billable toggle (Admin only)
  GET    /time-entries/daily-progress          — F2 timer bar badge data (Member only)
  POST   /time-entries/work-start-response     — F1 "start"/"not_now" response
  GET    /notifications/attendance             — paginated attendance notifications

Role enforcement:
  - PATCH settings: Admin only (Addendum §4.1)
  - GET daily-progress: Member only — PRD-ADD-03 (Admin/Manager exempt from tracking)
  - POST work-start-response: Member only — PRD-ADD-03
  - GET attendance notifications: any workspace member; scope filtered in service
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.schemas.attendance import (
    AttendanceNotificationsListResponse,
    DailyProgressResponse,
    WorkspaceBillableSettingsUpdate,
    WorkspaceBillableSettingsResponse,
    WorkspaceAttendanceSettingsUpdate,
    WorkspaceAttendanceSettingsResponse,
    WorkStartRequest,
    WorkStartResponse,
)
from app.services import attendance_service
from app.services import time_entry_service

router = APIRouter(tags=["Attendance"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_workspace_or_404(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    """Fetch a non-deleted workspace or raise 404."""
    from fastapi import HTTPException
    workspace = await db.get(Workspace, workspace_id)
    if not workspace or workspace.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )
    return workspace


# ── PATCH /workspaces/{workspace_id}/attendance-settings ──────────────────────

@router.patch(
    "/workspaces/{workspace_id}/attendance-settings",
    response_model=WorkspaceAttendanceSettingsResponse,
)
async def update_attendance_settings(
    workspace_id: uuid.UUID,
    body: WorkspaceAttendanceSettingsUpdate,
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Configure workspace attendance tracking settings.
    Addendum §4.1, PRD-ADD-01 through PRD-ADD-04.

    Admin only. Partial PATCH — only fields provided in the body are updated.

    Fields:
      attendance_enabled:    Master switch. When False, F1/F2 jobs skip this workspace.
      attendance_mode:       'fixed_schedule' or 'flexible_hours' (workspace-wide).
      work_start_time:       HH:MM trigger time for F1 prompt/reminder.
      daily_required_hours:  Daily hour target for F2 shortfall detection.
      off_days:              List of ints 0-6 (0=Sunday). F1+F2 suspended on these days.
    """
    workspace = await _get_workspace_or_404(db, workspace_id)
    updated = await attendance_service.update_attendance_settings(
        db=db,
        workspace=workspace,
        attendance_enabled=body.attendance_enabled,
        attendance_mode=body.attendance_mode,
        work_start_time=body.work_start_time,
        daily_required_hours=body.daily_required_hours,
        off_days=body.off_days,
    )
    await db.flush()
    return WorkspaceAttendanceSettingsResponse.model_validate(updated)


# ── PATCH /workspaces/{workspace_id}/billable-settings ────────────────────────

@router.patch(
    "/workspaces/{workspace_id}/billable-settings",
    response_model=WorkspaceBillableSettingsResponse,
)
async def update_billable_settings(
    workspace_id: uuid.UUID,
    body: WorkspaceBillableSettingsUpdate,
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle workspace-wide billable tracking.
    Addendum §4.1, PRD-ADD-05, PRD-ADD-06.

    Admin only.

    is_billable=False: rate computation short-circuits to None for all new entries.
    is_billable=True:  full rate hierarchy restored using existing stored rate data.
    Existing time entry billable_amount_cents snapshots are NEVER modified (PRD-ADD-06).
    """
    workspace = await _get_workspace_or_404(db, workspace_id)
    updated = await attendance_service.update_billable_settings(
        db=db,
        workspace=workspace,
        is_billable=body.is_billable,
    )
    await db.flush()
    return WorkspaceBillableSettingsResponse.model_validate(updated)


# ── GET /time-entries/daily-progress ──────────────────────────────────────────

@router.get(
    "/time-entries/daily-progress",
    response_model=DailyProgressResponse,
)
async def get_daily_progress(
    workspace_id: uuid.UUID,
    # Member only — PRD-ADD-03: Admin/Manager are exempt from attendance tracking
    member: WorkspaceMember = Depends(require_role("member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return today's logged hours vs daily target for the Timer Bar badge.
    Addendum §4.2, §6.4.

    Member role only (PRD-ADD-03 — Admin/Manager are attendance-exempt).

    Option B pacing formula (Risk 3):
      on_pace = True when target is still mathematically achievable by midnight,
                or when attendance tracking is disabled / no target is set.

    Frontend uses daily_required_hours != null to decide whether to render the badge.
    Polling interval: 30s (implemented in frontend hook, Addendum §4.5).
    """
    workspace = await _get_workspace_or_404(db, workspace_id)
    result = await attendance_service.get_daily_progress(
        db=db,
        workspace=workspace,
        user_id=current_user.id,
    )
    return DailyProgressResponse(**result)


# ── POST /time-entries/work-start-response ─────────────────────────────────────

@router.post(
    "/time-entries/work-start-response",
    response_model=WorkStartResponse,
    status_code=200,
)
async def work_start_response(
    workspace_id: uuid.UUID,
    body: WorkStartRequest,
    member: WorkspaceMember = Depends(require_role("member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Member response to the F1 work-start prompt modal.
    Addendum §4.2, §2.2.

    Member role only (PRD-ADD-03).

    response='not_now':
      Creates an attendance_notification record with the appropriate type.
      Computes late_by_minutes for fixed_schedule mode.
      Returns acknowledged=True, time_entry_id=None.

    response='start':
      Calls time_entry_service.start_timer() to create a new running entry.
      Returns acknowledged=True, time_entry_id=<new entry UUID>.
      project_id is required when response='start' (validated by schema).
    """
    workspace = await _get_workspace_or_404(db, workspace_id)

    # Handle "not_now" notification creation in attendance_service
    service_result = await attendance_service.record_work_start_response(
        db=db,
        workspace=workspace,
        user_id=current_user.id,
        response=body.response,
        project_id=body.project_id,
        task_id=body.task_id,
    )

    if body.response == "start":
        # Delegate timer start to time_entry_service (RULE B-06 layering)
        entry, _, _, _ = await time_entry_service.start_timer(
            db=db,
            user_id=current_user.id,
            workspace_id=workspace_id,
            caller_role=member.role,
            project_id=body.project_id,
            task_id=body.task_id,
            description=None,
            tag_ids=[],
            billable=workspace.is_billable,
            force=False,
        )
        service_result["time_entry_id"] = entry.id
        service_result["message"] = "Timer started successfully."

    return WorkStartResponse(**service_result)


# ── GET /notifications/attendance ──────────────────────────────────────────────

@router.get(
    "/notifications/attendance",
    response_model=AttendanceNotificationsListResponse,
)
async def list_attendance_notifications(
    workspace_id: uuid.UUID,
    scope: Literal["self", "managed"] = Query(
        "self",
        description=(
            "'self' returns only notifications where recipient=caller. "
            "'managed' returns all workspace attendance notifications (Admin/Manager only)."
        ),
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member", "viewer")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Paginated attendance notifications for the caller.
    Addendum §4.4.

    scope='self' (default): notifications where recipient_user_id = caller.
    scope='managed': ALL workspace attendance notifications (Admin/Manager only).
      Returns 403 if a Member/Viewer requests managed scope.

    Ordered newest-first. Includes total, unread_count, page, per_page.
    """
    result = await attendance_service.get_attendance_notifications(
        db=db,
        workspace_id=workspace_id,
        caller_user_id=current_user.id,
        caller_role=member.role,
        recipient_scope=scope,
        page=page,
        per_page=per_page,
    )
    return AttendanceNotificationsListResponse(**result)
