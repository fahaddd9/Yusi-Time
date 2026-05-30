"""
Auth service — all authentication business logic.

Five functions, each matching a use case from PRD v1.3 §3.2 and TRD v1.2 §6.6:
  register          → email/password signup, auto-creates workspace + admin membership
  login             → credential validation, returns token pair
  refresh_tokens    → validates refresh token, returns new access token
  initiate_password_reset → creates reset token, emails link (silent on unknown email)
  reset_password    → consumes token, updates password hash

Design decisions:
  - db.flush() after creates to get database-assigned IDs before commit
  - Silent return on unknown email in forgot-password (prevents user enumeration)
  - All prior reset tokens deleted before issuing a new one
  - Token is marked used=True immediately on successful reset (one-time use)
  - Email lookup uses LOWER() to be case-insensitive
"""

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.password_reset_token import PasswordResetToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    generate_secure_token,
)
from app.utils import email as email_util
from app.core.config import get_settings

settings = get_settings()


async def register(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
) -> dict:
    """
    Create a new user with their own workspace (admin role).

    Steps:
      1. Reject if email already exists (case-insensitive)
      2. Hash password with Argon2
      3. Create User, Workspace, WorkspaceMember
      4. flush() to get database IDs
      5. Return access_token + refresh_token + user + workspace objects
    """
    # 1. Check for duplicate email (case-insensitive)
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
            headers={"code": "EMAIL_ALREADY_EXISTS"},
        )

    # 2. Hash password
    pw_hash = hash_password(password)

    # 3. Create entities
    user = User(
        email=email.lower(),
        password_hash=pw_hash,
        full_name=full_name,
        is_active=True,
    )
    db.add(user)

    workspace = Workspace(name=f"{full_name}'s Workspace")
    db.add(workspace)

    # 4. Flush to get IDs before creating the member join
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="admin",
    )
    db.add(member)
    await db.flush()

    # 5. Generate tokens
    access_token = create_access_token(str(user.id), settings)
    refresh_token = create_refresh_token(str(user.id), settings)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user,
        "workspace": workspace,
    }


async def login(
    db: AsyncSession,
    email: str,
    password: str,
) -> dict:
    """
    Validate credentials and return a token pair.

    Raises 401 INVALID_CREDENTIALS on any failure — never distinguishes
    between "user not found" and "wrong password" to prevent enumeration.
    """
    # Fetch user by lowercase email
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"code": "INVALID_CREDENTIALS"},
        )

    if not verify_password(password, user.password_hash or ""):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"code": "INVALID_CREDENTIALS"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Account is deactivated",
            headers={"code": "INVALID_CREDENTIALS"},
        )

    # Fetch all workspaces this user belongs to
    ws_result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == user.id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspaces = ws_result.scalars().all()

    access_token = create_access_token(str(user.id), settings)
    refresh_token = create_refresh_token(str(user.id), settings)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user,
        "workspaces": workspaces,
    }


async def refresh_tokens(
    db: AsyncSession,
    refresh_token_str: str,
) -> dict:
    """
    Validate a refresh token (from HttpOnly cookie) and issue a new access token.
    Does NOT rotate the refresh token — one long-lived refresh token per session.
    """
    # verify_refresh_token raises 401 on failure
    payload = verify_refresh_token(refresh_token_str, settings.jwt_refresh_secret)

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"code": "UNAUTHENTICATED"},
        )

    access_token = create_access_token(str(user.id), settings)
    return {"access_token": access_token}


async def initiate_password_reset(
    db: AsyncSession,
    email: str,
) -> None:
    """
    Send a password reset link.
    IMPORTANT: Returns silently if no account exists for this email.
    This prevents user enumeration — the API response is identical whether
    the email exists or not.
    """
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        return  # Silent — do not reveal whether account exists

    # Delete all prior reset tokens for this user
    await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )

    # Create new token
    token_value = generate_secure_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_value,
        expires_at=expires_at,
        used=False,
    )
    db.add(reset_token)
    await db.flush()

    # Send email (prints to console in development)
    await email_util.send_reset_email(user.email, token_value)


async def reset_password(
    db: AsyncSession,
    token: str,
    new_password: str,
) -> dict:
    """
    Consume a password reset token and set a new password.

    Raises 400 BAD_REQUEST if:
      - Token not found
      - Token already used
      - Token expired
    """
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    )
    reset_token = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if (
        not reset_token
        or reset_token.used
        or reset_token.expires_at <= now
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
            headers={"code": "BAD_REQUEST"},
        )

    # Fetch user and update password
    user = await db.get(User, reset_token.user_id)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
            headers={"code": "BAD_REQUEST"},
        )

    user.password_hash = hash_password(new_password)
    reset_token.used = True
    await db.flush()

    return {"message": "Password reset successfully"}
