"""
Attendance & Push Subscription Pydantic schemas.

Addendum §4.1 — WorkspaceAttendanceSettings, WorkspaceBillableSettings
Addendum §4.2 — WorkStartRequest, WorkStartResponse, DailyProgressResponse
Addendum §4.3 — PushSubscriptionCreate, PushSubscriptionResponse
Addendum §4.4 — AttendanceNotificationResponse
Addendum §4.5 — Response schema notes (ConfigDict from_attributes=True, RULE B-04)

All schemas use Pydantic V2 with model_config = ConfigDict(from_attributes=True).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Workspace Attendance Settings ──────────────────────────────────────────────

class WorkspaceAttendanceSettingsUpdate(BaseModel):
    """
    PATCH /workspaces/{id}/attendance-settings request body.
    Addendum §4.1 — Admin only.

    Cross-field validation:
    - off_days values must all be in 0–6 (PRD-ADD-04)
    - daily_required_hours must be > 0 if provided (Addendum §3.1 CHECK)
    - work_start_time must be valid HH:MM string if provided
    - attendance_mode must be one of the two allowed values (PRD-ADD-02b)
    """
    attendance_enabled: Optional[bool] = None
    attendance_mode: Optional[Literal["fixed_schedule", "flexible_hours"]] = None
    # HH:MM 24-hour format string — stored as TIME column in DB
    work_start_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    daily_required_hours: Optional[float] = Field(None, gt=0, le=24)
    # 0=Sunday, 1=Monday, ..., 6=Saturday (Addendum §2.1)
    off_days: Optional[list[int]] = None

    @model_validator(mode="after")
    def validate_off_days_range(self) -> "WorkspaceAttendanceSettingsUpdate":
        """off_days values must be integers 0–6 (Addendum §4.1 error spec)."""
        if self.off_days is not None:
            for day in self.off_days:
                if day not in range(7):
                    raise ValueError(
                        f"off_days contains invalid value {day!r}; "
                        "each value must be an integer 0 (Sunday) through 6 (Saturday)"
                    )
        return self


class WorkspaceAttendanceSettingsResponse(BaseModel):
    """
    Response for PATCH /workspaces/{id}/attendance-settings.
    Addendum §4.1, §4.5 (ConfigDict from_attributes=True, RULE B-04).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attendance_enabled: bool
    attendance_mode: str
    # Serialized to HH:MM string for API consumers; None if not set
    work_start_time: Optional[time] = None
    daily_required_hours: Optional[float] = None
    off_days: list[int]


class WorkspaceBillableSettingsUpdate(BaseModel):
    """
    PATCH /workspaces/{id}/billable-settings request body.
    Addendum §4.1 — Admin only.
    is_billable=false suppresses rate computation workspace-wide (PRD-ADD-05).
    Existing stored rate data is NEVER deleted on toggle (PRD-ADD-05, PRD-ADD-06).
    """
    is_billable: bool


class WorkspaceBillableSettingsResponse(BaseModel):
    """
    Response for PATCH /workspaces/{id}/billable-settings.
    Addendum §4.1, §4.5.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_billable: bool


# ── Daily Progress (F2) ────────────────────────────────────────────────────────

class DailyProgressResponse(BaseModel):
    """
    Response for GET /time-entries/daily-progress.
    Addendum §4.2, §4.5.

    Option B pacing formula (approved by human supervisor, Risk 3):
      on_pace = True  if mathematically possible to still hit the target
                       (seconds_until_midnight >= required_seconds - logged_seconds)
      on_pace = True  if attendance_enabled=False or daily_required_hours is None
                       (no target set — frontend renders no indicator at all)

    Frontend checks daily_required_hours != null to decide whether to render
    the Timer Bar badge at all (Addendum §4.5).
    """
    hours_logged_today: float
    daily_required_hours: Optional[float] = None
    # True when target is achievable or not applicable; False when impossible
    on_pace: bool


# ── Work Start Response (F1) ────────────────────────────────────────────────────

class WorkStartRequest(BaseModel):
    """
    POST /time-entries/work-start-response request body.
    Addendum §4.2.

    response="start": creates a new time entry (project_id required)
    response="not_now": creates an attendance_notification record and dismisses
    """
    response: Literal["start", "not_now"]
    # Required when response="start" (Addendum §4.2)
    project_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def validate_start_requires_project(self) -> "WorkStartRequest":
        """project_id is required when response == 'start' (Addendum §4.2)."""
        if self.response == "start" and self.project_id is None:
            raise ValueError("project_id is required when response is 'start'")
        return self


class WorkStartResponse(BaseModel):
    """
    Response for POST /time-entries/work-start-response.
    Addendum §4.2.
    """
    model_config = ConfigDict(from_attributes=True)

    acknowledged: bool
    # Populated only when response="start" — the newly created time entry ID
    time_entry_id: Optional[uuid.UUID] = None
    message: str


# ── Attendance Notifications ────────────────────────────────────────────────────

class AttendanceNotificationResponse(BaseModel):
    """
    Item in GET /notifications/attendance response.
    Addendum §4.4, §4.5.

    notification_type values (Addendum §3.2):
      'work_start_missed'        — Fixed Schedule: Member didn't respond to prompt
      'flexible_reminder_missed' — Flexible Hours: Member at zero hours at reminder time
      'daily_hours_shortfall'    — End-of-day: Member logged < daily_required_hours
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    # Subject Member whose attendance is tracked
    user_id: uuid.UUID
    notification_type: str
    # The recipient of this notification (may differ from user_id for shortfall)
    recipient_user_id: uuid.UUID
    related_date: date
    # Minutes late (work_start_missed only, when triggered by late arrival)
    late_by_minutes: Optional[int] = None
    # Hours actually logged (daily_hours_shortfall only)
    hours_logged: Optional[float] = None
    # For UI rendering: populated dynamically by the service
    user_full_name: Optional[str] = None
    daily_required_hours: Optional[float] = None
    is_read: bool
    created_at: datetime


class AttendanceNotificationsListResponse(BaseModel):
    """Paginated wrapper for attendance notifications list. Addendum §4.4."""
    data: list[AttendanceNotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int


# ── Push Subscriptions (F1 push delivery) ─────────────────────────────────────

class PushSubscriptionCreate(BaseModel):
    """
    POST /users/me/push-subscriptions request body.
    Addendum §4.3.

    endpoint: browser-provided push service URL
    p256dh_key: ECDH public key (base64url-encoded) for payload encryption
    auth_key: authentication secret (base64url-encoded)
    """
    endpoint: str = Field(..., min_length=1)
    p256dh_key: str = Field(..., min_length=1)
    auth_key: str = Field(..., min_length=1)


class PushSubscriptionResponse(BaseModel):
    """
    Response for POST /users/me/push-subscriptions.
    Addendum §4.3, §4.5.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    endpoint: str
    created_at: datetime
