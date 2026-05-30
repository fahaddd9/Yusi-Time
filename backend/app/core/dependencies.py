"""
FastAPI injectable dependencies.

Three dependency tiers:
  1. get_current_user   — any authenticated user (Bearer token required)
  2. get_workspace_member — user must be a member of the target workspace
  3. require_role(*roles) — member must hold one of the specified roles

Usage examples:
  @router.get("/me")
  async def me(user: User = Depends(get_current_user)): ...

  @router.get("/workspaces/{workspace_id}/members")
  async def list_members(member: WorkspaceMember = Depends(require_role("admin","manager"))): ...
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_access_token
from app.core.config import get_settings
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from uuid import UUID

settings = get_settings()

# auto_error=False → we raise our own structured 401, not FastAPI's generic one
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer access token from Authorization header.
    Returns the active User ORM object.
    Raises HTTP 401 UNAUTHENTICATED if:
      - No Authorization header is present
      - Token is invalid / expired
      - User doesn't exist or is_active=False (anonymized account)
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"code": "UNAUTHENTICATED"},
        )
    # verify_access_token raises its own 401 on failure
    payload = verify_access_token(credentials.credentials, settings.jwt_secret)
    user = await db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
            headers={"code": "UNAUTHENTICATED"},
        )
    return user


async def get_workspace_member(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember:
    """
    Verify that the current user is a member of the requested workspace.
    Returns their WorkspaceMember record (which carries their role).
    Raises HTTP 404 NOT_FOUND if they are not a member — intentionally
    indistinguishable from "workspace doesn't exist" to prevent enumeration.
    """
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )
    return member


def require_role(*roles: str):
    """
    Role-gate factory. Returns a FastAPI dependency that:
      1. Calls get_workspace_member (which calls get_current_user internally)
      2. Checks that member.role is in the allowed roles list
      3. Raises HTTP 403 FORBIDDEN otherwise

    Usage:
      Depends(require_role("admin"))
      Depends(require_role("admin", "manager"))
    """
    async def _require_role(
        member: WorkspaceMember = Depends(get_workspace_member),
    ) -> WorkspaceMember:
        if member.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
                headers={"code": "FORBIDDEN"},
            )
        return member

    return _require_role
