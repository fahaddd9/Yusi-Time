"""
Workspace Pydantic schemas — API Spec v1.1 §5 · DB Schema v2.0 §4.3.

Schema hierarchy:
  WorkspaceSummary        — lightweight, used in auth responses and list views
  WorkspaceListItem       — extends summary with role + member_count
  WorkspaceDetail         — full settings for Admin/Manager/Member (includes financial)
  WorkspaceDetailViewer   — financial fields ABSENT (not None, completely excluded)
  WorkspaceUpdate         — PATCH payload, all optional, cross-field validation

Financial visibility rule (TRD v1.2 §6.3):
  Viewers must NOT see default_hourly_rate_cents or currency.
  Use WorkspaceDetailViewer for role='viewer', WorkspaceDetail for all others.
  Router selects schema via: caller_role == 'viewer'

Rounding validation rule:
  rounding_mode != 'none' requires rounding_interval_minutes to be set.
  Validated in WorkspaceUpdate @model_validator.

Idle detection rule:
  idle_detection_enabled=True requires idle_timeout_minutes to be set.
  Validated in WorkspaceUpdate @model_validator.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator
import uuid


# ── Shared base ────────────────────────────────────────────────────────────────

class WorkspaceSummary(BaseModel):
    """Lightweight workspace info — used in auth responses and list views."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    created_at: datetime


class WorkspaceListItem(BaseModel):
    """
    Item returned by GET /workspaces — includes the calling user's role.
    member_count is populated via a subquery in workspace_service.
    """
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    role: str  # caller's role in this workspace
    member_count: int
    created_at: datetime


# ── Full detail schemas ────────────────────────────────────────────────────────

class WorkspaceDetail(BaseModel):
    """
    Full workspace settings — returned for Admin, Manager, Member callers.
    Includes financial fields (default_hourly_rate_cents, currency).
    """
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    default_timezone: str
    date_format: str
    currency: str
    default_hourly_rate_cents: Optional[int] = None
    rounding_mode: str
    rounding_interval_minutes: Optional[int] = None
    mandatory_description: bool
    max_timer_duration_seconds: int
    past_entry_limit_days: int
    lock_period_days: int
    approval_workflow_enabled: bool
    idle_detection_enabled: bool
    idle_timeout_minutes: Optional[int] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WorkspaceDetailViewer(BaseModel):
    """
    Workspace settings for Viewer role — financial fields COMPLETELY ABSENT
    (not None, not zero — the keys do not appear in the JSON output at all).
    TRD v1.2 §6.3: Viewers must not see billing configuration.
    """
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    default_timezone: str
    date_format: str
    # currency and default_hourly_rate_cents intentionally omitted
    rounding_mode: str
    rounding_interval_minutes: Optional[int] = None
    mandatory_description: bool
    max_timer_duration_seconds: int
    past_entry_limit_days: int
    lock_period_days: int
    approval_workflow_enabled: bool
    idle_detection_enabled: bool
    idle_timeout_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Update request ─────────────────────────────────────────────────────────────

VALID_DATE_FORMATS = {"MM/DD/YYYY", "DD/MM/YYYY"}
VALID_ROUNDING_MODES = {"none", "nearest", "up", "down"}
VALID_ROUNDING_INTERVALS = {1, 5, 6, 10, 15, 30}
VALID_IDLE_TIMEOUTS = {1, 2, 5, 10, 15}


class WorkspaceUpdate(BaseModel):
    """
    PATCH /workspaces/{id} payload.

    All fields are optional — only provided fields are updated (PATCH semantics).

    Cross-field validation:
      - rounding_mode != 'none' requires rounding_interval_minutes
      - idle_detection_enabled=True requires idle_timeout_minutes
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    logo_url: Optional[str] = Field(None)
    default_timezone: Optional[str] = None
    date_format: Optional[Literal["MM/DD/YYYY", "DD/MM/YYYY"]] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    default_hourly_rate_cents: Optional[int] = Field(None, ge=0)
    rounding_mode: Optional[Literal["none", "nearest", "up", "down"]] = None
    rounding_interval_minutes: Optional[Literal[1, 5, 6, 10, 15, 30]] = None
    mandatory_description: Optional[bool] = None
    max_timer_duration_seconds: Optional[int] = Field(None, gt=0)
    past_entry_limit_days: Optional[int] = Field(None, ge=0)
    lock_period_days: Optional[int] = Field(None, ge=0)
    approval_workflow_enabled: Optional[bool] = None
    idle_detection_enabled: Optional[bool] = None
    idle_timeout_minutes: Optional[Literal[1, 2, 5, 10, 15]] = None

    @model_validator(mode="after")
    def validate_rounding_consistency(self) -> "WorkspaceUpdate":
        """rounding_mode != 'none' requires rounding_interval_minutes."""
        if self.rounding_mode and self.rounding_mode != "none":
            if self.rounding_interval_minutes is None:
                raise ValueError(
                    "rounding_interval_minutes is required when rounding_mode is not 'none'"
                )
        return self

    @model_validator(mode="after")
    def validate_idle_consistency(self) -> "WorkspaceUpdate":
        """idle_detection_enabled=True requires idle_timeout_minutes."""
        if self.idle_detection_enabled is True:
            if self.idle_timeout_minutes is None:
                raise ValueError(
                    "idle_timeout_minutes is required when idle_detection_enabled is true"
                )
        return self
