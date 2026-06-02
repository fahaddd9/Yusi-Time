"""
Member service — Phase 2 · API Spec v1.1 §6 · TRD v1.2 §6.6.

Functions:
  list_members  — paginated join of workspace_members + users
  change_role   — admin check, sole-admin guard, audit log
  remove_member — sole-admin guard, delete membership

Business rules:
  - new_role cannot be 'admin'. Admin is only created via workspace creation.
    Enforced at schema level (Literal) AND here as a 400 guard.
  - Sole-admin protection: if the target is the only Admin in the workspace,
    both demotion and removal raise 403 SOLE_ADMIN.
  - change_role logs to audit_logs with old_values={'role':old} new_values={'role':new}.
  - Super Admin bypass is handled upstream in get_workspace_member / require_role.
    This service only receives already-validated member objects.
"""

import uuid as _uuid
from math import ceil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.member import MemberResponse, PaginatedMemberResponse


async def _count_admins(db: AsyncSession, workspace_id: _uuid.UUID) -> int:
    """Return the number of Admin members in a workspace."""
    result = await db.execute(
        select(func.count(WorkspaceMember.user_id)).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role == "admin",
        )
    )
    return result.scalar_one()


async def list_members(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    page: int = 1,
    per_page: int = 25,
) -> PaginatedMemberResponse:
    """
    Return a paginated list of members for a workspace, joined with user data.

    All roles can call this endpoint (member+ permission).
    """
    offset = (page - 1) * per_page

    # Total count
    count_result = await db.execute(
        select(func.count(WorkspaceMember.user_id)).where(
            WorkspaceMember.workspace_id == workspace_id
        )
    )
    total = count_result.scalar_one()

    # Paginated rows
    rows_result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.joined_at)
        .offset(offset)
        .limit(per_page)
    )
    rows = rows_result.all()

    items = [
        MemberResponse(
            user_id=member.user_id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role=member.role,
            joined_at=member.joined_at,
        )
        for member, user in rows
    ]

    return PaginatedMemberResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=ceil(total / per_page) if total > 0 else 1,
    )


async def change_role(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    target_user_id: _uuid.UUID,
    new_role: str,
    actor_user_id: _uuid.UUID,
) -> MemberResponse:
    """
    Change a member's role. Admin-only.

    Validation:
      1. new_role cannot be 'admin' → 400 BAD_REQUEST
      2. If target is the only Admin and being demoted → 403 SOLE_ADMIN
      3. Update role, write audit log

    Returns the updated member's data.
    """
    if new_role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot promote to admin role via API",
            headers={"code": "BAD_REQUEST"},
        )

    # Fetch target membership
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
            headers={"code": "NOT_FOUND"},
        )
    member, user = row

    # Sole-admin protection
    if member.role == "admin":
        admin_count = await _count_admins(db, workspace_id)
        if admin_count <= 1:
            raise HTTPException(
                status_code=403,
                detail="Cannot demote the sole Admin of a workspace",
                headers={"code": "SOLE_ADMIN"},
            )

    old_role = member.role
    member.role = new_role

    # Audit log
    audit = AuditLog(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action="role_change",
        entity_type="workspace_member",
        entity_id=target_user_id,
        old_values={"role": old_role},
        new_values={"role": new_role},
    )
    db.add(audit)
    await db.flush()

    return MemberResponse(
        user_id=member.user_id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=member.role,
        joined_at=member.joined_at,
    )


async def remove_member(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    target_user_id: _uuid.UUID,
) -> None:
    """
    Remove a member from a workspace. Admin-only.

    Raises 403 SOLE_ADMIN if removing the only Admin.
    Raises 404 NOT_FOUND if user is not a member of this workspace.
    """
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
            headers={"code": "NOT_FOUND"},
        )

    # Sole-admin protection
    if member.role == "admin":
        admin_count = await _count_admins(db, workspace_id)
        if admin_count <= 1:
            raise HTTPException(
                status_code=403,
                detail="Cannot remove the sole Admin of a workspace",
                headers={"code": "SOLE_ADMIN"},
            )

    await db.delete(member)
    await db.flush()
