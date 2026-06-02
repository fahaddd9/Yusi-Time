"""
Members router — API Spec v1.1 §6.

Endpoints (all scoped to /workspaces/{workspace_id}/members):
  GET    /workspaces/{workspace_id}/members               — list members (member+)
  PATCH  /workspaces/{workspace_id}/members/{user_id}     — change role (admin only)
  DELETE /workspaces/{workspace_id}/members/{user_id}     — remove member (admin only)
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_workspace_member, require_role
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.member import MemberResponse, PaginatedMemberResponse, RoleUpdateRequest
from app.services import member_service

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["members"])


@router.get("", response_model=PaginatedMemberResponse)
async def list_members(
    workspace_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
) -> PaginatedMemberResponse:
    """
    GET /workspaces/{workspace_id}/members — paginated list of all members.

    Available to all workspace roles (viewer+).
    """
    return await member_service.list_members(
        db=db,
        workspace_id=workspace_id,
        page=page,
        per_page=per_page,
    )


@router.patch("/{target_user_id}", response_model=MemberResponse)
async def change_member_role(
    workspace_id: UUID,
    target_user_id: UUID,
    data: RoleUpdateRequest,
    member: WorkspaceMember = Depends(require_role("admin")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """
    PATCH /workspaces/{workspace_id}/members/{user_id} — change a member's role.

    Admin only. new_role cannot be 'admin'. Sole-admin demotion is blocked.
    Logs to audit_logs with old/new role values.
    """
    return await member_service.change_role(
        db=db,
        workspace_id=workspace_id,
        target_user_id=target_user_id,
        new_role=data.new_role,
        actor_user_id=current_user.id,
    )


@router.delete("/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: UUID,
    target_user_id: UUID,
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    DELETE /workspaces/{workspace_id}/members/{user_id} — remove a member.

    Admin only. Cannot remove the sole Admin of a workspace.
    """
    await member_service.remove_member(
        db=db,
        workspace_id=workspace_id,
        target_user_id=target_user_id,
    )
