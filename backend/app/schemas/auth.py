"""
Auth request/response Pydantic schemas — API Spec v1.1 §3.

Validator design notes:
  - email is normalized to lowercase on validation (Pydantic EmailStr does basic format check)
  - password must be 8–72 chars (72 = bcrypt/Argon2 practical max)
  - full_name is stripped of leading/trailing whitespace; minimum 2 chars after strip
  - Responses use model_config with from_attributes=True where needed
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import uuid
from datetime import datetime


# ── Requests ───────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str = Field(..., min_length=2, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("full_name must be at least 2 characters after stripping whitespace")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=72)


# ── Responses ──────────────────────────────────────────────────────────────

class TokenPair(BaseModel):
    """Embedded in signup/login responses. refresh_token is sent via HttpOnly cookie,
    not in this payload — this field is for documentation only."""
    access_token: str
    token_type: str = "bearer"


class WorkspaceSummaryEmbedded(BaseModel):
    """Minimal workspace info returned inside auth responses."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None


class UserEmbedded(BaseModel):
    """Minimal user info returned inside auth responses."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None


class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserEmbedded
    workspace: WorkspaceSummaryEmbedded


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserEmbedded
    workspaces: list[WorkspaceSummaryEmbedded]


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
