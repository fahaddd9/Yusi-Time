"""
Invites router — API Spec v1.1 §7.

Endpoints:
  POST   /workspaces/{workspace_id}/invites         — create invite (admin only)
  GET    /workspaces/{workspace_id}/invites         — list active invites (admin only)
  DELETE /workspaces/{workspace_id}/invites/{token} — revoke invite (admin only)
  GET    /invites/{token}                           — public invite info (no auth)
  POST   /invites/{token}/accept                    — accept invite (authenticated)

The workspace-scoped endpoints are on the workspace_router prefix.
The public /invites/* endpoints use a separate router prefix registered in main.py.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.invite import (
    InviteCreateRequest,
    InvitePublicResponse,
    InviteResponse,
    PaginatedInviteResponse,
)
from app.services import invite_service

# Workspace-scoped invite endpoints (admin only)
workspace_invites_router = APIRouter(
    prefix="/workspaces/{workspace_id}/invites",
    tags=["invites"],
)

# Public invite endpoints (no workspace prefix)
public_invites_router = APIRouter(
    prefix="/invites",
    tags=["invites"],
)


@workspace_invites_router.post(
    "",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    workspace_id: UUID,
    data: InviteCreateRequest,
    member: WorkspaceMember = Depends(require_role("admin")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InviteResponse:
    """
    POST /workspaces/{workspace_id}/invites — create a new invite.

    Admin only. role cannot be 'admin'. Token is cryptographically random.
    Expires in 7 days. Logs invite_generated to audit_logs.
    """
    return await invite_service.create_invite(
        db=db,
        workspace_id=workspace_id,
        data=data,
        created_by_user_id=current_user.id,
    )


@workspace_invites_router.get("", response_model=PaginatedInviteResponse)
async def list_invites(
    workspace_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> PaginatedInviteResponse:
    """
    GET /workspaces/{workspace_id}/invites — list active (pending) invites.

    Admin only. Active = not expired AND not used AND not revoked.
    """
    return await invite_service.list_invites(
        db=db,
        workspace_id=workspace_id,
        page=page,
        per_page=per_page,
    )


@workspace_invites_router.delete(
    "/{token}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invite(
    workspace_id: UUID,
    token: str,
    member: WorkspaceMember = Depends(require_role("admin")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    DELETE /workspaces/{workspace_id}/invites/{token} — revoke a pending invite.

    Admin only. Sets revoked=True. Cannot revoke already-used invites.
    Logs invite_revoked to audit_logs.
    """
    await invite_service.revoke_invite(
        db=db,
        workspace_id=workspace_id,
        token=token,
        actor_user_id=current_user.id,
    )


@public_invites_router.get("/{token}", response_model=InvitePublicResponse)
async def get_invite_public(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvitePublicResponse:
    """
    GET /invites/{token} — public endpoint, no authentication required.

    Returns workspace context for the invite acceptance page.
    Raises 400 with specific error codes for expired/used/revoked states.
    """
    return await invite_service.get_invite_public(db=db, token=token)


@public_invites_router.post(
    "/{token}/accept",
    status_code=status.HTTP_200_OK,
)
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    POST /invites/{token}/accept — accept an invite (authenticated).

    Creates workspace membership and marks invite as used in one atomic flush.
    Raises 409 ALREADY_MEMBER if the user is already in the workspace.
    """
    await invite_service.accept_invite(
        db=db,
        token=token,
        current_user_id=current_user.id,
    )
    return {"message": "Invite accepted successfully"}
