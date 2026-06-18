"""
Time Entry Pydantic schemas — API Spec v1.1 §12, §2 (TimeEntryObject, RoundingResult).

Two response variants per Viewer data isolation rule (PRD §4, API Spec §1.11):
  - TimeEntryObject       — full response (Admin / Manager / Member)
  - TimeEntryObjectViewer — financial fields ABSENT (not None, absent from model)

RoundingResult is ALWAYS included in stop / create / update responses.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ─── Shared sub-object: tag inside a time entry ───────────────────────────────

class TagInEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str | None


# ─── RoundingResult — API Spec §2 ─────────────────────────────────────────────

class RoundingResultSchema(BaseModel):
    """
    Returned alongside every time entry save operation (stop, create, update).
    Frontend uses this to show the mandatory rounding toast (PRD §7).
    """
    raw_seconds: int
    rounded_seconds: int
    rounding_mode: str          # none | nearest | up | down
    rounding_interval_minutes: int | None


# ─── Full response object (Admin / Manager / Member) ──────────────────────────

class TimeEntryObject(BaseModel):
    """
    Full time entry response including financial fields.
    Used for Admin, Manager, and Member roles.
    API Spec §2 TimeEntryObject.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    project_id: uuid.UUID
    project_name: str
    project_color: str | None
    task_id: uuid.UUID | None
    task_name: str | None
    description: str | None
    billable: bool
    status: str                 # draft | running | pending | approved
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    tags: list[TagInEntry] = Field(default_factory=list)
    # Financial fields — present for Admin/Manager/Member
    hourly_rate: str | None     # decimal string e.g. "75.00" or null
    billable_amount: str | None # decimal string e.g. "75.00" or null
    created_at: datetime
    updated_at: datetime


# ─── Viewer response object (financial fields ABSENT) ─────────────────────────

class TimeEntryObjectViewer(BaseModel):
    """
    Viewer-safe response — financial fields are completely absent from this model
    (not None, not hidden via CSS — they do not exist in the payload).
    API Spec §1.11 Viewer Data Isolation.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    project_id: uuid.UUID
    project_name: str
    project_color: str | None
    task_id: uuid.UUID | None
    task_name: str | None
    description: str | None
    billable: bool
    status: str
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    tags: list[TagInEntry] = Field(default_factory=list)
    # hourly_rate and billable_amount are INTENTIONALLY absent
    created_at: datetime
    updated_at: datetime


# ─── Request schemas ───────────────────────────────────────────────────────────

class StartTimerRequest(BaseModel):
    """POST /time-entries/start — API Spec §12."""
    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    description: str | None = Field(None, max_length=500)
    billable: bool | None = None   # defaults to project.default_billable if None
    tag_ids: list[uuid.UUID] = Field(default_factory=list)
    force: bool = False            # stop running timer if one exists


class StopTimerRequest(BaseModel):
    """POST /time-entries/{id}/stop — API Spec §12."""
    idle_end_time: datetime | None = None  # PRD §3.3.3 Idle Detection


class CreateManualEntryRequest(BaseModel):
    """POST /time-entries — API Spec §12."""
    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    start_time: datetime
    end_time: datetime
    description: str | None = Field(None, max_length=500)
    billable: bool | None = None
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class UpdateEntryRequest(BaseModel):
    """PATCH /time-entries/{id} — all fields optional, API Spec §12."""
    project_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    description: str | None = Field(None, max_length=500)
    billable: bool | None = None
    tag_ids: list[uuid.UUID] | None = None


# ─── Response wrappers ────────────────────────────────────────────────────────

class StopTimerResponse(BaseModel):
    """Stop timer returns entry + mandatory rounding result (API Spec §12)."""
    data: TimeEntryObject
    rounding: RoundingResultSchema


class StopTimerResponseViewer(BaseModel):
    data: TimeEntryObjectViewer
    rounding: RoundingResultSchema


class CreateManualEntryResponse(BaseModel):
    """Manual entry create returns entry + rounding + overlap flag (API Spec §12)."""
    data: TimeEntryObject
    rounding: RoundingResultSchema
    has_overlap: bool


class CreateManualEntryResponseViewer(BaseModel):
    data: TimeEntryObjectViewer
    rounding: RoundingResultSchema
    has_overlap: bool


class UpdateEntryResponse(BaseModel):
    """Update entry returns entry + rounding (API Spec §12)."""
    data: TimeEntryObject
    rounding: RoundingResultSchema


class UpdateEntryResponseViewer(BaseModel):
    data: TimeEntryObjectViewer
    rounding: RoundingResultSchema


class GetCurrentTimerResponse(BaseModel):
    """GET /time-entries/current — wraps nullable entry."""
    data: TimeEntryObject | None


class GetCurrentTimerResponseViewer(BaseModel):
    data: TimeEntryObjectViewer | None


class ListEntriesResponse(BaseModel):
    """Cursor-paginated list — API Spec §1.5."""
    data: list[TimeEntryObject]
    next_cursor: str | None
    limit: int


class ListEntriesResponseViewer(BaseModel):
    data: list[TimeEntryObjectViewer]
    next_cursor: str | None
    limit: int
