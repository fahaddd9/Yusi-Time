"""
FastAPI injectable dependencies.

Three dependency tiers:
  1. get_current_user      — any authenticated user (Bearer token required)
  2. get_workspace_member  — user must be a member of the target workspace
                             OR is_superadmin=True (synthetic member injected)
  3. require_role(*roles)  — member must hold one of the specified roles
                             OR is_superadmin=True (bypass unconditionally)
  4. get_superadmin_user   — caller must be a Super Admin (pattern established for
                             future Super Admin-only endpoints; Phase 1.5)

Super Admin bypass architecture (MASTER_PROMPT §11 · DB Schema v2.2):
  - is_superadmin is a parallel track outside the workspace_role enum.
  - get_workspace_member short-circuits the DB membership query and returns a
    synthetic WorkspaceMember(role='admin') so callers never need to branch.
  - require_role() checks is_superadmin first; if True, the role list is
    irrelevant and the synthetic member is returned immediately.
  - No endpoint, no workspace Admin, no API surface can set is_superadmin.
    Only a direct database UPDATE by a system operator can do so.

Usage examples:
  @router.get("/me")
  async def me(user: User = Depends(get_current_user)): ...

  @router.get("/workspaces/{workspace_id}/members")
  async def list_members(member: WorkspaceMember = Depends(require_role("admin", "manager"))): ...

  # Future Super Admin-only endpoint:
  @router.get("/admin/users")
  async def admin_list_users(sa_user: User = Depends(get_superadmin_user)): ...
"""

import uuid as _uuid
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


def _make_synthetic_member(workspace_id: UUID, user_id: _uuid.UUID) -> WorkspaceMember:
    """
    Build an in-memory WorkspaceMember with role='admin' for Super Admins.

    This object is NEVER persisted and never touches the workspace_members table.
    It exists solely so that downstream service functions that receive a member
    argument behave correctly — they see role='admin' and proceed without error.

    Implementation note: SQLAlchemy mapped attributes are Python *class-level*
    descriptors. Both direct assignment and object.__setattr__ call the descriptor
    __set__ method, which requires _sa_instance_state to be initialised (which
    __new__ does not do). The correct bypass is to write directly into the
    instance's __dict__, which completely skips the descriptor protocol.

    DB Schema v2.2 · MASTER_PROMPT §11.
    """
    synthetic = WorkspaceMember.__new__(WorkspaceMember)
    synthetic.__dict__.update({
        "workspace_id": workspace_id,
        "user_id": user_id,
        "role": "admin",
    })
    return synthetic


async def get_workspace_member(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember:
    """
    Verify that the current user is a member of the requested workspace.

    Super Admin bypass (MASTER_PROMPT §11):
      If current_user.is_superadmin is True, skip the membership DB query
      entirely and return a synthetic WorkspaceMember(role='admin').
      The workspace_members table is never queried for Super Admins.

    For regular users:
      Returns their WorkspaceMember record (which carries their role).
      Raises HTTP 404 NOT_FOUND if they are not a member — intentionally
      indistinguishable from "workspace doesn't exist" to prevent enumeration.
    """
    # Super Admin bypass — synthetic member, no DB query
    if current_user.is_superadmin:
        return _make_synthetic_member(workspace_id, current_user.id)

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
      2. If the user is a Super Admin, returns the synthetic admin member
         immediately without checking the roles list (MASTER_PROMPT §11)
      3. Otherwise checks that member.role is in the allowed roles list
      4. Raises HTTP 403 FORBIDDEN if not in the list

    Usage:
      Depends(require_role("admin"))
      Depends(require_role("admin", "manager"))
    """
    async def _require_role(
        current_user: User = Depends(get_current_user),
        member: WorkspaceMember = Depends(get_workspace_member),
    ) -> WorkspaceMember:
        # Super Admin bypasses ALL role checks unconditionally (MASTER_PROMPT §11)
        if current_user.is_superadmin:
            return member  # already synthetic admin from get_workspace_member
        if member.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
                headers={"code": "FORBIDDEN"},
            )
        return member

    return _require_role


async def get_superadmin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency for Super Admin-only endpoints (future use — Phase 7.5).

    Pattern established in Phase 1.5 so future endpoints can simply use:
      Depends(get_superadmin_user)

    No endpoints currently use this dependency. It exists to establish the
    pattern and verify the dependency chain works correctly. (MASTER_PROMPT §11)

    Raises HTTP 403 FORBIDDEN if the user is not a Super Admin.
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required",
            headers={"code": "FORBIDDEN"},
        )
    return current_user
