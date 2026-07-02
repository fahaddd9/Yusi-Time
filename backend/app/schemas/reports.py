"""
Report Pydantic schemas — Phase 7.

Authority sources:
  - API Spec v1.1 §14 (all response shapes, field lists)
  - PRD §3.8 (business rules, Viewer isolation)
  - Addendum §2.4 PRD-ADD-05 (workspace.is_billable suppression)

DUAL SUPPRESSION LAYERS (non-negotiable):
  Layer 1 — Workspace billable toggle (PRD-ADD-05):
    When workspace.is_billable = false, ALL roles (including Admin) receive the
    Viewer-equivalent schema (no financial fields). This is configuration-based,
    not role-based.

  Layer 2 — Viewer financial isolation (RULE U-01):
    When caller role == 'viewer', financial fields are ABSENT (not null, not 0).
    Uses a separate schema class — never a single schema with nullable fields.

  The service function selects the correct schema class based on both checks.
  Frontend enforces the same rule in the component layer (Step 7.3/7.4).

All schemas use Pydantic V2 ConfigDict(from_attributes=True).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Saved Report Views ──────────────────────────────────────────────────────────

class SavedReportViewCreate(BaseModel):
    """
    POST /reports/saved-views request body.
    API Spec v1.1 §14 — report_type must match CHECK constraint values.
    DB Schema v2.1 §5 — allowed values: 'summary' | 'detailed' | 'weekly'.
    """
    name: str = Field(..., min_length=1, max_length=255)
    report_type: Literal["summary", "detailed", "weekly"]
    # Arbitrary filter state — any keys accepted, validated by service
    filters: dict[str, Any] = Field(default_factory=dict)


class SavedReportViewResponse(BaseModel):
    """
    Response for list/create saved-views operations.
    API Spec v1.1 §14.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    report_type: str
    filters: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ── Summary Report ──────────────────────────────────────────────────────────────

class SummaryRowBase(BaseModel):
    """
    One grouped row in the Summary report — base fields visible to all roles.
    API Spec v1.1 §14 GET /reports/summary response.
    """
    model_config = ConfigDict(from_attributes=True)

    group_key: Optional[str]    # UUID as string, or None for un-grouped
    group_label: Optional[str]  # Human-readable name (project name, user name, etc.)
    total_seconds: int
    total_hours: float
    non_billable_hours: float
    entry_count: int


class SummaryRowFull(SummaryRowBase):
    """
    Summary row WITH financial fields — for Admin/Manager when is_billable=True.
    RULE U-01: Viewer never receives this schema.
    Addendum PRD-ADD-05: non-billable workspace never receives this schema.
    """
    billable_seconds: int
    billable_hours: float
    total_billable_amount: Optional[str]  # Decimal as string, e.g. "3000.00"


class SummaryRowViewer(SummaryRowBase):
    """
    Summary row WITHOUT financial fields — for Viewer role OR non-billable workspace.
    RULE U-01 / PRD-ADD-05: billable_seconds, billable_hours, total_billable_amount
    are ABSENT from this schema entirely.
    API Spec v1.1 §14 (Viewer data isolation).
    """
    # No additional fields — financial fields are absent by design


class SummarySummaryFull(BaseModel):
    """Summary footer — full (Admin/Manager in billable workspace)."""
    model_config = ConfigDict(from_attributes=True)

    total_hours: float
    total_billable_amount: Optional[str]
    date_from: date
    date_to: date


class SummarySummaryViewer(BaseModel):
    """Summary footer — Viewer / non-billable workspace (no financial fields)."""
    model_config = ConfigDict(from_attributes=True)

    total_hours: float
    date_from: date
    date_to: date


class SummaryReportResponseFull(BaseModel):
    """Full Summary report response — Admin/Manager in billable workspace."""
    data: list[SummaryRowFull]
    summary: SummarySummaryFull


class SummaryReportResponseViewer(BaseModel):
    """Viewer / non-billable workspace Summary report response."""
    data: list[SummaryRowViewer]
    summary: SummarySummaryViewer


# ── Detailed Report ─────────────────────────────────────────────────────────────

class TagRef(BaseModel):
    """Minimal tag reference embedded in detailed entries."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class DetailedEntryBase(BaseModel):
    """
    One time entry row in the Detailed report — base fields visible to all roles.
    API Spec v1.1 §14 GET /reports/detailed.
    Viewers see: hours, description, project, task, tags only (PRD §3.8).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    project_id: uuid.UUID
    project_name: Optional[str]
    client_id: Optional[uuid.UUID]
    client_name: Optional[str]
    task_id: Optional[uuid.UUID]
    task_name: Optional[str]
    description: Optional[str]
    billable: bool
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    tags: list[TagRef]


class DetailedEntryFull(DetailedEntryBase):
    """
    Detailed entry WITH financial snapshot fields.
    Admin/Manager in billable workspace only.
    RULE U-01 / PRD-ADD-05.
    """
    hourly_rate_cents: Optional[int]
    billable_amount_cents: Optional[int]


class DetailedEntryViewer(DetailedEntryBase):
    """
    Detailed entry WITHOUT financial fields.
    Viewer role or non-billable workspace.
    hourly_rate_cents and billable_amount_cents are ABSENT.
    RULE U-01 / PRD-ADD-05.
    """


class DetailedSummaryFull(BaseModel):
    """Detailed report footer — with financials."""
    total_hours: float
    total_billable_amount: Optional[str]


class DetailedSummaryViewer(BaseModel):
    """Detailed report footer — no financials."""
    total_hours: float


class DetailedReportResponseFull(BaseModel):
    """Full Detailed report response."""
    data: list[DetailedEntryFull]
    next_cursor: Optional[str]
    limit: int
    summary: DetailedSummaryFull


class DetailedReportResponseViewer(BaseModel):
    """Viewer / non-billable Detailed report response."""
    data: list[DetailedEntryViewer]
    next_cursor: Optional[str]
    limit: int
    summary: DetailedSummaryViewer


# ── Weekly Report ───────────────────────────────────────────────────────────────

class WeeklyDayCell(BaseModel):
    """
    One day's data within a user row in the Weekly report.
    Financial fields present or absent based on role/billable toggle.
    API Spec v1.1 §14 GET /reports/weekly.
    """
    total_seconds: int
    total_hours: float
    entry_count: int


class WeeklyDayCellFull(WeeklyDayCell):
    """Day cell WITH billable hours (Admin/Manager, billable workspace)."""
    billable_hours: float


class WeeklyDayCellViewer(WeeklyDayCell):
    """Day cell WITHOUT billable hours (Viewer / non-billable workspace)."""


class WeeklyUserRowBase(BaseModel):
    """Base user row in the Weekly grid."""
    user_id: uuid.UUID
    user_name: str
    avatar_url: Optional[str]
    total_seconds: int
    total_hours: float


class WeeklyUserRowFull(WeeklyUserRowBase):
    """
    Weekly user row WITH financial fields.
    Admin/Manager in billable workspace.
    API Spec v1.1 §14 — billable_hours, total_billable_amount present.
    """
    billable_hours: float
    total_billable_amount: Optional[str]
    days: dict[str, WeeklyDayCellFull]  # keyed by "YYYY-MM-DD"


class WeeklyUserRowViewer(WeeklyUserRowBase):
    """
    Weekly user row WITHOUT financial fields.
    Viewer role or non-billable workspace.
    billable_hours and total_billable_amount ABSENT (RULE U-01 / PRD-ADD-05).
    """
    days: dict[str, WeeklyDayCellViewer]  # keyed by "YYYY-MM-DD"


class WeeklyTotalsDayFull(BaseModel):
    """Per-day column totals — with billable hours."""
    total_hours: float
    billable_hours: float


class WeeklyTotalsDayViewer(BaseModel):
    """Per-day column totals — without billable hours."""
    total_hours: float


class WeeklyTotalsFull(BaseModel):
    """
    Grand totals block — with financials.
    API Spec v1.1 §14 grand_total_billable_amount present.
    """
    by_day: dict[str, WeeklyTotalsDayFull]
    grand_total_hours: float
    grand_total_billable_amount: Optional[str]


class WeeklyTotalsViewer(BaseModel):
    """Grand totals block — no financials. RULE U-01 / PRD-ADD-05."""
    by_day: dict[str, WeeklyTotalsDayViewer]
    grand_total_hours: float
    # grand_total_billable_amount ABSENT


class WeeklyReportDataFull(BaseModel):
    """Weekly report response data wrapper — full financial view."""
    date_from: date
    date_to: date
    days: list[str]    # ordered list of "YYYY-MM-DD" strings
    rows: list[WeeklyUserRowFull]
    totals: WeeklyTotalsFull


class WeeklyReportDataViewer(BaseModel):
    """Weekly report response data wrapper — Viewer / non-billable."""
    date_from: date
    date_to: date
    days: list[str]
    rows: list[WeeklyUserRowViewer]
    totals: WeeklyTotalsViewer


class WeeklyReportResponseFull(BaseModel):
    """Full Weekly report API response envelope."""
    data: WeeklyReportDataFull


class WeeklyReportResponseViewer(BaseModel):
    """Viewer / non-billable Weekly report API response envelope."""
    data: WeeklyReportDataViewer


# ── Query parameter models (shared across all report types) ─────────────────────

class ReportDateRangeParams(BaseModel):
    """
    Validated date range parameters shared across Summary, Detailed, Weekly.
    Used for structured parameter parsing in service functions.
    """
    date_from: date
    date_to: date
