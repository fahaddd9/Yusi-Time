"""
Member Pydantic schemas — API Spec v1.1 §6.

Used by:
  GET  /workspaces/{id}/members         → PaginatedMemberResponse
  PATCH /workspaces/{id}/members/{uid}  → RoleUpdateRequest → MemberResponse
  DELETE /workspaces/{id}/members/{uid} → 204 No Content
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel
import uuid


class MemberResponse(BaseModel):
    """Full member info returned by list and update endpoints."""
    model_config = {"from_attributes": True}

    user_id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    joined_at: datetime


class RoleUpdateRequest(BaseModel):
    """
    PATCH /workspaces/{id}/members/{user_id} payload.

    new_role cannot be 'admin' — admins are only created via the initial
    workspace creation (first user becomes admin). Service enforces this.
    """
    new_role: Literal["manager", "member", "viewer"]


class PaginatedMemberResponse(BaseModel):
    """Paginated wrapper for member list."""
    items: list[MemberResponse]
    total: int
    page: int
    per_page: int
    pages: int
