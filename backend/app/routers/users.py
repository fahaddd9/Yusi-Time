"""
Users router — API Spec v1.1 §4.

Endpoints:
  GET    /users/me — get current user profile
  PATCH  /users/me — update profile (all optional)
  DELETE /users/me — anonymize account (cannot be undone)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserPublic, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    """
    GET /users/me — return the authenticated user's full profile.

    Includes is_superadmin field per MASTER_PROMPT §11.
    """
    return await user_service.get_me(current_user)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """
    PATCH /users/me — update profile fields.

    All fields are optional. Only provided fields are updated (PATCH semantics).
    """
    return await user_service.update_me(db=db, user=current_user, data=data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    DELETE /users/me — anonymize the user's account.

    Overwrites PII in-place (email, full_name, google_id, avatar_url).
    Sets is_active=False. Removes all workspace memberships.

    Blocked if the user is the sole Admin in any non-deleted workspace.
    Cannot be undone — the data is gone immediately.
    """
    await user_service.delete_me(db=db, user=current_user)
