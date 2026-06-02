"""
User service — Phase 2 · API Spec v1.1 §4 · TRD v1.2 §6.6.

Functions:
  get_me     — return UserPublic for the current user
  update_me  — PATCH profile fields (all optional, PATCH semantics)
  delete_me  — anonymize the account (never hard-delete)

Anonymization rules (DB Schema v2.0 §4.1):
  - email → "deleted-{short_uuid}@anonymous.local"
  - full_name → "Deleted User {short_uuid}"
  - google_id → None
  - password_hash → None
  - is_active → False

delete_me guard:
  If the user is the sole Admin in any non-deleted workspace → 403 SOLE_ADMIN.
  They must transfer admin or delete the workspace first.
"""

import uuid as _uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete, func
from fastapi import HTTPException

from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.models.workspace import Workspace
from app.schemas.user import UserPublic, UserUpdate


async def get_me(user: User) -> UserPublic:
    """Return the UserPublic schema for the current user."""
    return UserPublic.model_validate(user)


async def update_me(
    db: AsyncSession,
    user: User,
    data: UserUpdate,
) -> UserPublic:
    """
    PATCH /users/me — update only the provided fields.

    All fields in UserUpdate are optional. Only fields present in the
    request body are updated (model_dump(exclude_unset=True)).
    """
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)

    await db.flush()
    # Refresh to pick up updated_at trigger
    await db.refresh(user)
    return UserPublic.model_validate(user)


async def delete_me(
    db: AsyncSession,
    user: User,
) -> None:
    """
    DELETE /users/me — anonymize the account, never hard-delete.

    Guard: if the user is the sole Admin in any non-deleted workspace,
    raise 403 SOLE_ADMIN. They must transfer Admin or delete the workspace first.

    Anonymization overwrites PII columns in-place, preserving referential
    integrity on time_entries, audit_logs, etc.
    """
    # Check: is this user the sole admin in any non-deleted workspace?
    admin_memberships_result = await db.execute(
        select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.role == "admin",
        )
    )
    admin_workspace_ids = admin_memberships_result.scalars().all()

    for ws_id in admin_workspace_ids:
        # Is the workspace deleted?
        ws = await db.get(Workspace, ws_id)
        if ws and ws.deleted_at is not None:
            continue  # Skip soft-deleted workspaces

        # Count admins in this workspace
        count_result = await db.execute(
            select(func.count(WorkspaceMember.user_id)).where(
                WorkspaceMember.workspace_id == ws_id,
                WorkspaceMember.role == "admin",
            )
        )
        admin_count = count_result.scalar_one()
        if admin_count <= 1:
            raise HTTPException(
                status_code=403,
                detail=(
                    "You are the sole Admin of one or more workspaces. "
                    "Transfer Admin to another member or delete the workspace first."
                ),
                headers={"code": "SOLE_ADMIN"},
            )

    # Remove all workspace memberships
    await db.execute(
        sa_delete(WorkspaceMember).where(WorkspaceMember.user_id == user.id)
    )

    # Anonymize in-place
    short_uuid = str(user.id)[:8]
    user.email = f"deleted-{short_uuid}@anonymous.local"
    user.full_name = f"Deleted User {short_uuid}"
    user.google_id = None
    user.password_hash = None
    user.avatar_url = None
    user.is_active = False

    await db.flush()
