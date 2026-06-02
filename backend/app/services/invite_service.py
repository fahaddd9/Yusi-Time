"""
Invite service — Phase 2 · API Spec v1.1 §7 · TRD v1.2 §6.6.

Functions:
  create_invite     — generates token, sets 7-day expiry, audit log
  list_invites      — active only (not expired, not used, not revoked)
  get_invite_public — validates token state, returns workspace context
  revoke_invite     — sets revoked=True, audit log
  accept_invite     — atomic: create membership + mark used; 409 if already member

Error codes:
  INVITE_EXPIRED  — invite has passed its expires_at timestamp
  INVITE_USED     — invite was already accepted by someone
  INVITE_REVOKED  — invite was revoked by an Admin
  ALREADY_MEMBER  — the accepting user is already a member of this workspace

Security:
  - token is secrets.token_urlsafe(32) — cryptographically random, URL-safe
  - get_invite_public is intentionally unauthenticated (allows sharing by URL)
  - accept_invite requires authentication (current_user must be logged in)
  - role cannot be 'admin' — enforced at schema + service layer
"""

import uuid as _uuid
import secrets
from datetime import datetime, timezone, timedelta
from math import ceil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.invite import Invite
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.audit_log import AuditLog
from app.schemas.invite import (
    InviteCreateRequest,
    InviteResponse,
    InvitePublicResponse,
    PaginatedInviteResponse,
)

INVITE_EXPIRY_DAYS = 7


async def create_invite(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    data: InviteCreateRequest,
    created_by_user_id: _uuid.UUID,
) -> InviteResponse:
    """
    Create an invite for the given workspace and email.

    role cannot be 'admin' — validated at schema level (Literal) and here.
    Token is cryptographically random. Expires in 7 days.
    Logs invite_generated to audit_logs.
    """
    if data.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot invite with role 'admin'",
            headers={"code": "BAD_REQUEST"},
        )

    # Check workspace exists and isn't deleted
    workspace = await db.get(Workspace, workspace_id)
    if not workspace or workspace.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )

    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)

    invite = Invite(
        workspace_id=workspace_id,
        email=data.email.lower(),
        role=data.role,
        token=token,
        expires_at=now + timedelta(days=INVITE_EXPIRY_DAYS),
        created_by_user_id=created_by_user_id,
    )
    db.add(invite)

    # Audit log
    audit = AuditLog(
        workspace_id=workspace_id,
        actor_user_id=created_by_user_id,
        action="invite_generated",
        entity_type="invite",
        new_values={"email": data.email.lower(), "role": data.role},
    )
    db.add(audit)
    await db.flush()

    return InviteResponse.model_validate(invite)


async def list_invites(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    page: int = 1,
    per_page: int = 25,
) -> PaginatedInviteResponse:
    """
    List active invites for a workspace.

    Active = not expired AND not used AND not revoked.
    Only Admins can call this (enforced by require_role in router).
    """
    now = datetime.now(timezone.utc)

    base_filter = [
        Invite.workspace_id == workspace_id,
        Invite.expires_at > now,
        Invite.used.is_(False),
        Invite.revoked.is_(False),
    ]

    count_result = await db.execute(
        select(func.count(Invite.id)).where(*base_filter)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * per_page
    rows_result = await db.execute(
        select(Invite)
        .where(*base_filter)
        .order_by(Invite.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    invites = rows_result.scalars().all()

    return PaginatedInviteResponse(
        items=[InviteResponse.model_validate(inv) for inv in invites],
        total=total,
        page=page,
        per_page=per_page,
        pages=ceil(total / per_page) if total > 0 else 1,
    )


async def get_invite_public(
    db: AsyncSession,
    token: str,
) -> InvitePublicResponse:
    """
    Validate and return public invite information.

    Unauthenticated endpoint — returns workspace context for the invite page.
    Checks in order: exists → expired → used → revoked.

    Raises specific error codes per TRD v1.2 §6.6:
      INVITE_EXPIRED  — expires_at < now()
      INVITE_USED     — used = True
      INVITE_REVOKED  — revoked = True
    """
    result = await db.execute(
        select(Invite, Workspace)
        .join(Workspace, Workspace.id == Invite.workspace_id)
        .where(Invite.token == token)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(
            status_code=400,
            detail="Invite not found",
            headers={"code": "NOT_FOUND"},
        )
    invite, workspace = row

    now = datetime.now(timezone.utc)
    if invite.expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="This invite has expired",
            headers={"code": "INVITE_EXPIRED"},
        )
    if invite.used:
        raise HTTPException(
            status_code=400,
            detail="This invite has already been used",
            headers={"code": "INVITE_USED"},
        )
    if invite.revoked:
        raise HTTPException(
            status_code=400,
            detail="This invite has been revoked",
            headers={"code": "INVITE_REVOKED"},
        )

    return InvitePublicResponse(
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        workspace_logo_url=workspace.logo_url,
        role=invite.role,
        email=invite.email,
        expires_at=invite.expires_at,
    )


async def revoke_invite(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    token: str,
    actor_user_id: _uuid.UUID,
) -> None:
    """
    Revoke a pending invite. Admin only (enforced by router).

    Sets revoked=True and revoked_at=now().
    Logs invite_revoked to audit_logs.
    Raises 404 if the invite doesn't belong to this workspace or doesn't exist.
    Raises 400 if the invite is already used or revoked.
    """
    result = await db.execute(
        select(Invite).where(
            Invite.token == token,
            Invite.workspace_id == workspace_id,
        )
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(
            status_code=404,
            detail="Invite not found",
            headers={"code": "NOT_FOUND"},
        )
    if invite.used:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke an already-used invite",
            headers={"code": "BAD_REQUEST"},
        )
    if invite.revoked:
        raise HTTPException(
            status_code=400,
            detail="Invite is already revoked",
            headers={"code": "BAD_REQUEST"},
        )

    now = datetime.now(timezone.utc)
    invite.revoked = True
    invite.revoked_at = now

    audit = AuditLog(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action="invite_revoked",
        entity_type="invite",
        entity_id=invite.id,
        old_values={"email": invite.email, "role": invite.role},
    )
    db.add(audit)
    await db.flush()


async def accept_invite(
    db: AsyncSession,
    token: str,
    current_user_id: _uuid.UUID,
) -> None:
    """
    Accept an invite — atomically creates membership and marks the invite used.

    Steps:
    1. Validate invite state (same checks as get_invite_public)
    2. Check if caller is already a member → 409 ALREADY_MEMBER
    3. Create WorkspaceMember (with invited_by_user_id from invite)
    4. Set invite.used=True, invite.used_by_user_id, invite.used_at

    All changes in a single flush (atomic within the DB session transaction).
    """
    # Re-validate the invite state fully
    result = await db.execute(select(Invite).where(Invite.token == token))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(
            status_code=400,
            detail="Invite not found",
            headers={"code": "NOT_FOUND"},
        )

    now = datetime.now(timezone.utc)
    if invite.expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="This invite has expired",
            headers={"code": "INVITE_EXPIRED"},
        )
    if invite.used:
        raise HTTPException(
            status_code=400,
            detail="This invite has already been used",
            headers={"code": "INVITE_USED"},
        )
    if invite.revoked:
        raise HTTPException(
            status_code=400,
            detail="This invite has been revoked",
            headers={"code": "INVITE_REVOKED"},
        )

    # Check if the user's email matches the invite email
    from app.models.user import User
    user = await db.get(User, current_user_id)
    if not user or user.email.lower() != invite.email.lower():
        raise HTTPException(
            status_code=400,
            detail="This invite was sent to a different email address",
            headers={"code": "EMAIL_MISMATCH"},
        )

    # Check if already a member
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == invite.workspace_id,
            WorkspaceMember.user_id == current_user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="You are already a member of this workspace",
            headers={"code": "ALREADY_MEMBER"},
        )

    # Create membership
    membership = WorkspaceMember(
        workspace_id=invite.workspace_id,
        user_id=current_user_id,
        role=invite.role,
        invited_by_user_id=invite.created_by_user_id,
    )
    db.add(membership)

    # Mark invite as used
    invite.used = True
    invite.used_by_user_id = current_user_id
    invite.used_at = now

    await db.flush()
