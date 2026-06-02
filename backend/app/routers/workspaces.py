"""
Workspace router — API Spec v1.1 §5.

Endpoints:
  GET  /workspaces                    — list caller's workspaces
  GET  /workspaces/{workspace_id}     — get workspace detail
  PATCH /workspaces/{workspace_id}    — update settings (Admin only)
  DELETE /workspaces/{workspace_id}   — soft delete (Admin only)

Member and Invite sub-endpoints are in routers/members.py and routers/invites.py,
registered here with the same workspace_id path prefix so they appear grouped
in Swagger.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_workspace_member, require_role
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.workspace import WorkspaceDetail, WorkspaceDetailViewer, WorkspaceListItem, WorkspaceUpdate
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceListItem])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceListItem]:
    """
    GET /workspaces — list all workspaces the caller is a member of.

    Returns role and member_count for each workspace.
    Excludes soft-deleted workspaces.
    """
    return await workspace_service.get_user_workspaces(db=db, user_id=current_user.id)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetail | WorkspaceDetailViewer,
)
async def get_workspace(
    workspace_id: UUID,
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceDetail | WorkspaceDetailViewer:
    """
    GET /workspaces/{workspace_id} — get workspace detail.

    Returns WorkspaceDetailViewer (financial fields absent) for Viewer role.
    Returns WorkspaceDetail (all fields) for Admin, Manager, Member roles.
    """
    return await workspace_service.get_workspace(
        db=db,
        workspace_id=workspace_id,
        caller_role=member.role,
    )


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceDetail,
)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceDetail:
    """
    PATCH /workspaces/{workspace_id} — update workspace settings.

    Admin only. Applies only the fields present in the request body (PATCH semantics).
    Cross-field validation (rounding, idle detection) is done by WorkspaceUpdate schema.
    """
    return await workspace_service.update_workspace(
        db=db,
        workspace_id=workspace_id,
        data=data,
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    workspace_id: UUID,
    member: WorkspaceMember = Depends(require_role("admin")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    DELETE /workspaces/{workspace_id} — soft delete the workspace.

    Admin only. Sets deleted_at=now(). Notifies all members.
    Hard deletion (removing DB rows) occurs after 30 days via a scheduled job.
    """
    await workspace_service.soft_delete_workspace(
        db=db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
    )
