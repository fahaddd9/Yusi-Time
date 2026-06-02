"""
Invite Pydantic schemas — API Spec v1.1 §7.

Three tiers:
  InviteCreateRequest  — POST body (admin → create invite)
  InviteResponse       — admin-facing view (includes all fields, no raw token in list)
  InvitePublicResponse — unauthenticated GET /invites/{token} (workspace info only)
  PaginatedInviteResponse — paginated wrapper for list endpoint

Security notes:
  - InvitePublicResponse deliberately excludes the token itself to avoid
    echo-back in API responses. The token is only in the URL.
  - InviteResponse includes token so admin can copy/share it after creation.
  - role cannot be 'admin' — enforced at Literal level here and DB CHECK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr
import uuid


class InviteCreateRequest(BaseModel):
    """POST /workspaces/{id}/invites payload."""
    email: EmailStr
    role: Literal["manager", "member", "viewer"]


class InviteResponse(BaseModel):
    """
    Full invite record — returned to the Admin who created it or lists it.
    Includes the token so the Admin can share the invite URL.
    """
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    role: str
    token: str
    expires_at: datetime
    used: bool
    revoked: bool
    created_at: datetime


class InvitePublicResponse(BaseModel):
    """
    Response for GET /invites/{token} — unauthenticated, public endpoint.

    Contains only what the invitee needs to see: workspace context + role.
    Token is NOT echoed back in the response body — only used for the accept call.
    """
    workspace_id: uuid.UUID
    workspace_name: str
    workspace_logo_url: Optional[str] = None
    role: str
    email: str
    expires_at: datetime


class PaginatedInviteResponse(BaseModel):
    """Paginated wrapper for invite list (admin-only endpoint)."""
    items: list[InviteResponse]
    total: int
    page: int
    per_page: int
    pages: int
