"""
Workspace service — Phase 2 · API Spec v1.1 §5 · TRD v1.2 §6.6.

Functions:
  get_user_workspaces  — list all workspaces the caller is a member of
  get_workspace        — fetch one workspace, return role-appropriate schema
  update_workspace     — Admin only, PATCH fields, validate rounding/idle
  soft_delete_workspace — Admin only, sets deleted_at, notifies members, audit log

Business rules:
  - Soft-deleted workspaces (deleted_at IS NOT NULL) are excluded from lists
    and return 404 for all scoped endpoints.
  - Only Admin role can mutate workspace settings or delete.
  - Financial fields (default_hourly_rate_cents, currency) are excluded
    from responses for Viewer role (WorkspaceDetailViewer).
  - Approval workflow disable triggers handle_workflow_disabled in Phase 6.
    In Phase 2 we call a stub that does nothing.
"""

import uuid as _uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.audit_log import AuditLog
from app.schemas.workspace import (
    WorkspaceDetail,
    WorkspaceDetailViewer,
    WorkspaceListItem,
    WorkspaceUpdate,
)
from app.services import notification_service


async def get_user_workspaces(
    db: AsyncSession,
    user_id: _uuid.UUID,
) -> list[WorkspaceListItem]:
    """
    Return all non-deleted workspaces where user_id is a member.

    Each item includes the caller's role and total member_count (subquery).
    """
    # Subquery: member count per workspace
    member_count_sq = (
        select(
            WorkspaceMember.workspace_id,
            func.count(WorkspaceMember.user_id).label("member_count"),
        )
        .group_by(WorkspaceMember.workspace_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Workspace,
            WorkspaceMember.role,
            func.coalesce(member_count_sq.c.member_count, 0).label("member_count"),
        )
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .outerjoin(member_count_sq, member_count_sq.c.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == user_id,
            Workspace.deleted_at.is_(None),
        )
        .order_by(Workspace.created_at)
    )
    rows = result.all()

    return [
        WorkspaceListItem(
            id=ws.id,
            name=ws.name,
            logo_url=ws.logo_url,
            role=role,
            member_count=member_count,
            created_at=ws.created_at,
        )
        for ws, role, member_count in rows
    ]


async def get_workspace(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    caller_role: str,
) -> WorkspaceDetail | WorkspaceDetailViewer:
    """
    Fetch a non-deleted workspace and return the role-appropriate schema.

    Viewer → WorkspaceDetailViewer (financial fields absent)
    All other roles → WorkspaceDetail (full fields)
    """
    workspace = await db.get(Workspace, workspace_id)
    if not workspace or workspace.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )

    if caller_role == "viewer":
        return WorkspaceDetailViewer.model_validate(workspace)
    return WorkspaceDetail.model_validate(workspace)


async def update_workspace(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    data: WorkspaceUpdate,
) -> WorkspaceDetail:
    """
    PATCH workspace settings. Admin only (enforced by require_role in router).

    Applies only the fields that were explicitly provided in the request body.
    Rounding and idle cross-field validation is done by WorkspaceUpdate schema.

    If approval_workflow_enabled transitions True → False, future Phase 6
    will call approval_service.handle_workflow_disabled(). For Phase 2, we
    leave this as a stub comment.
    """
    workspace = await db.get(Workspace, workspace_id)
    if not workspace or workspace.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(workspace, field, value)

    # Phase 6 hook: if approval_workflow_enabled changed True → False,
    # call approval_service.handle_workflow_disabled(db, workspace_id)

    await db.flush()
    return WorkspaceDetail.model_validate(workspace)


async def soft_delete_workspace(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    actor_user_id: _uuid.UUID,
) -> None:
    """
    Soft-delete a workspace. Admin only (enforced by require_role in router).

    Steps:
    1. Set deleted_at = now()
    2. Notify all members with workspace_deleted event
    3. Write audit_log entry (action=workspace_soft_deleted)

    Hard deletion (removing DB rows) is done by a scheduled job after 30 days.
    """
    workspace = await db.get(Workspace, workspace_id)
    if not workspace or workspace.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )

    workspace.deleted_at = datetime.now(timezone.utc)

    # Notify all members
    await notification_service.create_for_all_members(
        db=db,
        workspace_id=workspace_id,
        event_type="workspace_deleted",
        title="Workspace scheduled for deletion",
        message=(
            f'The workspace "{workspace.name}" has been deleted by an Admin. '
            "All data will be permanently removed after 30 days."
        ),
        metadata={"workspace_name": workspace.name},
    )

    # Audit log
    audit = AuditLog(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action="workspace_soft_deleted",
        entity_type="workspace",
        entity_id=workspace_id,
        new_values={"deleted_at": str(workspace.deleted_at)},
    )
    db.add(audit)
    await db.flush()
