"""
Reports Router — Phase 7.

All 9 endpoints per API Spec v1.1 §14:
  GET  /reports/summary               — grouped summary (by project/user/client/tag)
  GET  /reports/summary/export        — CSV download of summary
  GET  /reports/detailed              — cursor-paginated entry list
  GET  /reports/detailed/export       — CSV download of detailed
  GET  /reports/weekly                — per-user, per-day grid (NEW v1.1)
  GET  /reports/weekly/export         — CSV download of weekly
  GET  /reports/saved-views           — list saved views for current user
  POST /reports/saved-views           — save a filter configuration
  DELETE /reports/saved-views/{id}    — delete a saved view

Role enforcement:
  - All report endpoints: any workspace member (require any role).
  - Admin/Manager: see all members + financial fields (when billable).
  - Member/Viewer: locked to own data at service layer (PITFALL 1).
  - Viewer: no financial fields in response (RULE U-01, enforced in service).
  - Non-billable workspace: no financial fields for ANY role (PRD-ADD-05).

Router → Service → Model layering strictly maintained.
Zero business logic in this file.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_workspace_member
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.reports import (
    SavedReportViewCreate,
    SavedReportViewResponse,
)
from app.services import report_service

router = APIRouter(tags=["Reports"])


# ── Helper: resolve caller metadata from dependencies ──────────────────────────

def _caller_meta(
    current_user: User,
    member: WorkspaceMember,
) -> tuple[str, uuid.UUID]:
    """Extract (role, user_id) from auth dependencies."""
    return member.role, current_user.id


# ── Summary Report ──────────────────────────────────────────────────────────────

@router.get("/reports/summary")
async def get_summary_report(
    workspace_id: uuid.UUID = Query(...),
    group_by: Literal["project", "user", "client", "tag"] = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    project_id: Optional[uuid.UUID] = Query(None),
    client_id: Optional[uuid.UUID] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    billable: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Grouped summary of hours and amounts.
    API Spec v1.1 §14 — PRD §3.8 Summary Report.

    Member isolation enforced at service layer.
    Financial fields suppressed for Viewer / non-billable workspace.
    """
    caller_role, caller_user_id = _caller_meta(current_user, member)
    result = await report_service.get_summary(
        db=db,
        workspace_id=workspace_id,
        caller_role=caller_role,
        caller_user_id=caller_user_id,
        group_by=group_by,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        client_id=client_id,
        user_id=user_id,
        billable=billable,
        status=status,
    )
    # Remove internal suppress flag before returning
    result.pop("suppress", None)
    return result


# ── Summary CSV Export ──────────────────────────────────────────────────────────

@router.get("/reports/summary/export")
async def export_summary_report(
    workspace_id: uuid.UUID = Query(...),
    group_by: Literal["project", "user", "client", "tag"] = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    project_id: Optional[uuid.UUID] = Query(None),
    client_id: Optional[uuid.UUID] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    billable: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    CSV download of Summary report.
    API Spec v1.1 §14 — same params as GET /reports/summary.
    Financial columns absent for Viewer / non-billable workspace (PITFALL 4).
    """
    caller_role, caller_user_id = _caller_meta(current_user, member)
    return await report_service.export_summary_csv(
        db=db,
        workspace_id=workspace_id,
        caller_role=caller_role,
        caller_user_id=caller_user_id,
        group_by=group_by,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        client_id=client_id,
        user_id=user_id,
        billable=billable,
        status=status,
    )


# ── Detailed Report ─────────────────────────────────────────────────────────────

@router.get("/reports/detailed")
async def get_detailed_report(
    workspace_id: uuid.UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    project_id: Optional[uuid.UUID] = Query(None),
    client_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    billable: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    tag_ids: Optional[list[uuid.UUID]] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("start_time"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Cursor-paginated list of individual time entries.
    API Spec v1.1 §14 GET /reports/detailed.

    Viewers: see hours, description, project, task, tags only (PRD §3.8).
    Financial fields suppressed for Viewer / non-billable workspace.
    Continue / Duplicate actions per row — wired in frontend Step 7.4.
    """
    caller_role, caller_user_id = _caller_meta(current_user, member)
    result = await report_service.get_detailed(
        db=db,
        workspace_id=workspace_id,
        caller_role=caller_role,
        caller_user_id=caller_user_id,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        client_id=client_id,
        task_id=task_id,
        user_id=user_id,
        billable=billable,
        status=status,
        tag_ids=tag_ids,
        cursor=cursor,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    result.pop("suppress", None)
    return result


# ── Detailed CSV Export ─────────────────────────────────────────────────────────

@router.get("/reports/detailed/export")
async def export_detailed_report(
    workspace_id: uuid.UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    project_id: Optional[uuid.UUID] = Query(None),
    client_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    billable: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    tag_ids: Optional[list[uuid.UUID]] = Query(None),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    CSV download of Detailed report.
    API Spec v1.1 §14 — financial columns absent for Viewer / non-billable (PITFALL 4).
    All entries exported (no pagination limit for export).
    """
    caller_role, caller_user_id = _caller_meta(current_user, member)
    return await report_service.export_detailed_csv(
        db=db,
        workspace_id=workspace_id,
        caller_role=caller_role,
        caller_user_id=caller_user_id,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        client_id=client_id,
        task_id=task_id,
        user_id=user_id,
        billable=billable,
        status=status,
        tag_ids=tag_ids,
    )


# ── Weekly Report ───────────────────────────────────────────────────────────────

@router.get("/reports/weekly")
async def get_weekly_report(
    workspace_id: uuid.UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    user_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    billable: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Per-user, per-day grid of hours for a date range.
    API Spec v1.1 §14 GET /reports/weekly — NEW v1.1.
    TRD §6.6 get_weekly_report.

    Authorization:
      - Admin/Manager: see all members' rows
      - Member/Viewer: auto-locked to own ID; other user_id → 403

    Date span: max 31 days → 400 if exceeded.
    Zero-hour days included in response.
    Financial fields suppressed for Viewer / non-billable workspace.
    """
    caller_role, caller_user_id = _caller_meta(current_user, member)
    result = await report_service.get_weekly_report(
        db=db,
        workspace_id=workspace_id,
        caller_role=caller_role,
        caller_user_id=caller_user_id,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        project_id=project_id,
        billable=billable,
    )
    result.pop("suppress", None)
    return result


# ── Weekly CSV Export ───────────────────────────────────────────────────────────

@router.get("/reports/weekly/export")
async def export_weekly_report(
    workspace_id: uuid.UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    user_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    billable: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    CSV download of Weekly report.
    API Spec v1.1 §14 GET /reports/weekly/export — NEW v1.1.
    One row per member. Financial column absent for Viewer / non-billable.
    """
    caller_role, caller_user_id = _caller_meta(current_user, member)
    return await report_service.export_weekly_csv(
        db=db,
        workspace_id=workspace_id,
        caller_role=caller_role,
        caller_user_id=caller_user_id,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        project_id=project_id,
        billable=billable,
    )


# ── Saved Views ─────────────────────────────────────────────────────────────────

@router.get("/reports/saved-views", response_model=list[SavedReportViewResponse])
async def list_saved_views(
    workspace_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> list[SavedReportViewResponse]:
    """
    List current user's saved report views for this workspace.
    API Spec v1.1 §14 GET /reports/saved-views.
    PRD §3.8: "private to their account".
    """
    views = await report_service.list_saved_views(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
    return [SavedReportViewResponse.model_validate(v) for v in views]


@router.post("/reports/saved-views", response_model=SavedReportViewResponse, status_code=201)
async def create_saved_view(
    workspace_id: uuid.UUID = Query(...),
    body: SavedReportViewCreate = ...,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> SavedReportViewResponse:
    """
    Save current filter configuration as a named view.
    API Spec v1.1 §14 POST /reports/saved-views.
    Raises 409 DUPLICATE_NAME if name already exists for this user.

    report_type CHECK: 'summary' | 'detailed' | 'weekly'
    — DB Schema v2.1 §5 (migration 0002).
    """
    view = await report_service.create_saved_view(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=body.name,
        report_type=body.report_type,
        filters=body.filters,
    )
    return SavedReportViewResponse.model_validate(view)


@router.delete("/reports/saved-views/{view_id}", status_code=204)
async def delete_saved_view(
    view_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Delete a saved view. Ownership verified at service layer.
    API Spec v1.1 §14 DELETE /reports/saved-views/{view_id}.
    Raises 404 if not found or not owned by current user.
    """
    await report_service.delete_saved_view(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        view_id=view_id,
    )
    return Response(status_code=204)
