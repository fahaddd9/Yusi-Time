"""
User Pydantic schemas — public-facing representations of the User model.

UserPublic is what GET /users/me returns.
UserUpdate is what PATCH /users/me accepts.
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime


class UserPublic(BaseModel):
    """Full user profile returned to the authenticated user.

    is_superadmin is always included — frontend reads this from GET /users/me
    to gate Super Admin UI elements (Phase 7.5). MASTER_PROMPT §11.
    """
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    weekly_hours_goal: Optional[int] = None
    is_active: bool
    is_superadmin: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """PATCH /users/me — all fields optional."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=1024)
    timezone: Optional[str] = Field(None, max_length=64)
    weekly_hours_goal: Optional[int] = Field(None, gt=0, le=168)
