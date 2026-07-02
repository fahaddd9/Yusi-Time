"""
Report Service — Phase 7.

All report query logic lives here. Routers call ONE function each;
zero business logic in routers (RULE B-06: Router → Service → Model).

Authority sources:
  - TRD v1.3 §6.6 (service function signatures and algorithm)
  - API Spec v1.1 §14 (response shapes, query params, error codes)
  - PRD §3.8 (feature requirements, Viewer access)
  - PRD §4 (role permission table)
  - DB Schema v2.0 §4.15 (saved_report_views table)
  - DB Schema v2.1 §5 (report_type CHECK constraint: 'summary'|'detailed'|'weekly')
  - Addendum §2.4 PRD-ADD-05 (workspace.is_billable suppression for ALL roles)

CRITICAL BUSINESS RULES (enforced at service layer — not just query filters):

  Rule 1 — Member data isolation:
    Members may only see their OWN time entries in all report types.
    Enforced by the query WHERE clause — not just a default filter the caller
    can override. A Member calling the API directly must still only see their data.

  Rule 2 — Viewer financial isolation (RULE U-01):
    billable_seconds, billable_hours, hourly_rate_cents, billable_amount_cents,
    total_billable_amount, grand_total_billable_amount are ABSENT from Viewer
    responses. Enforced by returning separate response schema instances.

  Rule 3 — Non-billable workspace (PRD-ADD-05):
    When workspace.is_billable = False, ALL roles receive the same suppressed
    schema as Viewer. This is workspace-configuration-based, not role-based.
    Check is_billable FIRST; Viewer check is secondary.

  Rule 4 — CSV export:
    Export functions call the same data-gathering logic as JSON endpoints,
    then stream as CSV. They apply the SAME role/billable suppression.
    Never a raw DB query that bypasses suppression.
"""

from __future__ import annotations

import base64
import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal, Optional

import pytz
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.project import Project
from app.models.saved_report_view import SavedReportView
from app.models.tag import Tag
from app.models.time_entry import TimeEntry
from app.models.time_entry_tag import TimeEntryTag
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cents_to_decimal_str(cents: Optional[int]) -> Optional[str]:
    """
    Convert stored integer cents to a 2-decimal-place string.
    Returns None if cents is None.
    PRD §3.7: billable amount displayed with currency symbol in frontend.
    This service returns the raw decimal string; formatting is frontend's job.
    """
    if cents is None:
        return None
    return str((Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _seconds_to_hours(seconds: int) -> float:
    """Convert seconds to hours, rounded to 2 decimal places."""
    return round(seconds / 3600, 2)


def _is_suppressed(workspace: Workspace, caller_role: str) -> bool:
    """
    Determine whether financial fields should be suppressed.

    PRD-ADD-05: Check is_billable FIRST (workspace-config).
    RULE U-01: Then check Viewer role.

    Returns True when financials must be suppressed (absent from response).
    """
    # PRD-ADD-05: non-billable workspace suppresses for ALL roles
    if not workspace.is_billable:
        return True
    # RULE U-01: Viewer always suppressed in billable workspaces too
    if caller_role == "viewer":
        return True
    return False


async def _get_workspace_or_403(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    """
    Fetch workspace, raise 404 if not found or deleted.
    Called by all report service functions as first step.
    """
    ws = await db.get(Workspace, workspace_id)
    if not ws or ws.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
            headers={"code": "NOT_FOUND"},
        )
    return ws


def _tz_day_bounds(day: date, tz_name: str) -> tuple[datetime, datetime]:
    """
    Return (start_of_day_utc, end_of_day_utc) for a calendar day in the
    workspace timezone.

    Report queries filter by date must use workspace timezone to determine
    correct UTC boundaries (PITFALL 6 in session prompt).
    """
    try:
        tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        tz = pytz.UTC

    naive_start = datetime(day.year, day.month, day.day, 0, 0, 0)
    naive_end = datetime(day.year, day.month, day.day, 23, 59, 59, 999999)
    start_utc = tz.localize(naive_start).astimezone(pytz.UTC).replace(tzinfo=timezone.utc)
    end_utc = tz.localize(naive_end).astimezone(pytz.UTC).replace(tzinfo=timezone.utc)
    return start_utc, end_utc


def _date_range_utc_bounds(
    date_from: date, date_to: date, tz_name: str
) -> tuple[datetime, datetime]:
    """
    Return (start_of_date_from, end_of_date_to) in UTC for a date range.
    TRD §6.6 — weekly report uses workspace timezone for date boundaries.
    PITFALL 6.
    """
    start_utc, _ = _tz_day_bounds(date_from, tz_name)
    _, end_utc = _tz_day_bounds(date_to, tz_name)
    return start_utc, end_utc


# ── Summary Report ──────────────────────────────────────────────────────────────

async def get_summary(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_role: str,
    caller_user_id: uuid.UUID,
    group_by: Literal["project", "user", "client", "tag"],
    date_from: date,
    date_to: date,
    project_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    billable: Optional[bool] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """
    Grouped summary of hours and amounts.
    TRD v1.3 §6.6 get_summary.

    Member isolation: Members are locked to their own user_id regardless of
    what user_id param was supplied. SERVICE layer — not just UI filter.
    Viewer / non-billable workspace: suppress financial fields via schema selection.

    Returns a dict with 'data' and 'summary' keys.
    Callers (router) wrap the dict in the correct response schema.
    """
    workspace = await _get_workspace_or_403(db, workspace_id)
    suppress = _is_suppressed(workspace, caller_role)

    # Rule 1 — Member data isolation (PRD §4 / PITFALL 1)
    # Enforced at the service layer; a Member/Viewer can NEVER see another member's data
    if caller_role in ("member", "viewer"):
        effective_user_id = caller_user_id
        # If caller passed a user_id that isn't their own, return 403
        if user_id is not None and user_id != caller_user_id:
            raise HTTPException(
                status_code=403,
                detail="Members can only view their own data",
                headers={"code": "FORBIDDEN"},
            )
    else:
        effective_user_id = user_id  # Admin/Manager: honour the filter param

    tz_name = workspace.default_timezone or "UTC"
    start_utc, end_utc = _date_range_utc_bounds(date_from, date_to, tz_name)

    # Base scalar aggregations — always computed
    sum_total_seconds = func.coalesce(func.sum(TimeEntry.duration_seconds), 0).label("total_seconds")
    sum_billable_seconds = func.coalesce(
        func.sum(
            case(
                (TimeEntry.billable == True, TimeEntry.duration_seconds),  # noqa: E712
                else_=0,
            )
        ),
        0,
    ).label("billable_seconds")
    sum_billable_amount = func.coalesce(
        func.sum(
            case(
                (TimeEntry.billable == True, TimeEntry.billable_amount_cents),  # noqa: E712
                else_=0,
            )
        ),
        0,
    ).label("billable_amount_cents")
    entry_count = func.count(TimeEntry.id).label("entry_count")

    # Build GROUP BY dimension
    if group_by == "project":
        group_col = TimeEntry.project_id
        label_col = Project.name
        stmt = (
            select(
                group_col.label("group_key"),
                label_col.label("group_label"),
                sum_total_seconds,
                sum_billable_seconds,
                sum_billable_amount,
                entry_count,
            )
            .join(Project, TimeEntry.project_id == Project.id, isouter=True)
            .where(
                TimeEntry.workspace_id == workspace_id,
                TimeEntry.start_time >= start_utc,
                TimeEntry.start_time <= end_utc,
                TimeEntry.duration_seconds.isnot(None),
            )
            .group_by(TimeEntry.project_id, Project.name)
        )
    elif group_by == "user":
        group_col = TimeEntry.user_id
        stmt = (
            select(
                group_col.label("group_key"),
                User.full_name.label("group_label"),
                sum_total_seconds,
                sum_billable_seconds,
                sum_billable_amount,
                entry_count,
            )
            .join(User, TimeEntry.user_id == User.id)
            .where(
                TimeEntry.workspace_id == workspace_id,
                TimeEntry.start_time >= start_utc,
                TimeEntry.start_time <= end_utc,
                TimeEntry.duration_seconds.isnot(None),
            )
            .group_by(TimeEntry.user_id, User.full_name)
        )
    elif group_by == "client":
        stmt = (
            select(
                Client.id.label("group_key"),
                Client.name.label("group_label"),
                sum_total_seconds,
                sum_billable_seconds,
                sum_billable_amount,
                entry_count,
            )
            .join(Project, TimeEntry.project_id == Project.id)
            .join(Client, Project.client_id == Client.id, isouter=True)
            .where(
                TimeEntry.workspace_id == workspace_id,
                TimeEntry.start_time >= start_utc,
                TimeEntry.start_time <= end_utc,
                TimeEntry.duration_seconds.isnot(None),
            )
            .group_by(Client.id, Client.name)
        )
    elif group_by == "tag":
        stmt = (
            select(
                Tag.id.label("group_key"),
                Tag.name.label("group_label"),
                sum_total_seconds,
                sum_billable_seconds,
                sum_billable_amount,
                entry_count,
            )
            .join(TimeEntryTag, TimeEntry.id == TimeEntryTag.time_entry_id, isouter=True)
            .join(Tag, TimeEntryTag.tag_id == Tag.id, isouter=True)
            .where(
                TimeEntry.workspace_id == workspace_id,
                TimeEntry.start_time >= start_utc,
                TimeEntry.start_time <= end_utc,
                TimeEntry.duration_seconds.isnot(None),
            )
            .group_by(Tag.id, Tag.name)
        )
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid group_by value: {group_by!r}. Must be project|user|client|tag",
            headers={"code": "VALIDATION_ERROR"},
        )

    # Apply optional filters
    if effective_user_id is not None:
        stmt = stmt.where(TimeEntry.user_id == effective_user_id)
    if project_id is not None:
        stmt = stmt.where(TimeEntry.project_id == project_id)
    if client_id is not None:
        stmt = stmt.where(
            Project.client_id == client_id
            if group_by in ("project", "user", "tag")
            else Client.id == client_id
        )
    if billable is not None:
        stmt = stmt.where(TimeEntry.billable == billable)
    if status is not None:
        stmt = stmt.where(TimeEntry.status == status)

    result = await db.execute(stmt)
    rows = result.fetchall()

    data = []
    total_seconds_sum = 0
    total_billable_cents = 0

    for row in rows:
        total_sec = int(row.total_seconds or 0)
        bill_sec = int(row.billable_seconds or 0)
        bill_cents = int(row.billable_amount_cents or 0)
        total_hours = _seconds_to_hours(total_sec)
        bill_hours = _seconds_to_hours(bill_sec)
        non_bill_hours = round(total_hours - bill_hours, 2)
        total_seconds_sum += total_sec
        total_billable_cents += bill_cents

        group_key_val = str(row.group_key) if row.group_key is not None else None

        if suppress:
            data.append({
                "group_key": group_key_val,
                "group_label": row.group_label,
                "total_seconds": total_sec,
                "total_hours": total_hours,
                "non_billable_hours": non_bill_hours,
                "entry_count": int(row.entry_count),
            })
        else:
            data.append({
                "group_key": group_key_val,
                "group_label": row.group_label,
                "total_seconds": total_sec,
                "total_hours": total_hours,
                "billable_seconds": bill_sec,
                "billable_hours": bill_hours,
                "non_billable_hours": non_bill_hours,
                "total_billable_amount": _cents_to_decimal_str(total_billable_cents) if not suppress else None,
                "entry_count": int(row.entry_count),
            })

    grand_total_hours = _seconds_to_hours(total_seconds_sum)

    if suppress:
        summary = {
            "total_hours": grand_total_hours,
            "date_from": date_from,
            "date_to": date_to,
        }
    else:
        summary = {
            "total_hours": grand_total_hours,
            "total_billable_amount": _cents_to_decimal_str(total_billable_cents),
            "date_from": date_from,
            "date_to": date_to,
        }

    return {"data": data, "summary": summary, "suppress": suppress}


# ── Detailed Report ─────────────────────────────────────────────────────────────

def _encode_cursor(entry_id: uuid.UUID, start_time: datetime) -> str:
    """Encode cursor from entry_id + start_time. Opaque to client."""
    raw = f"{entry_id}|{start_time.isoformat()}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[uuid.UUID, datetime]:
    """Decode cursor string. Raises 400 on malformed cursor."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        parts = raw.split("|", 1)
        entry_id = uuid.UUID(parts[0])
        start_time = datetime.fromisoformat(parts[1])
        return entry_id, start_time
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor",
            headers={"code": "BAD_REQUEST"},
        )


async def get_detailed(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_role: str,
    caller_user_id: uuid.UUID,
    date_from: date,
    date_to: date,
    project_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    task_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    billable: Optional[bool] = None,
    status: Optional[str] = None,
    tag_ids: Optional[list[uuid.UUID]] = None,
    cursor: Optional[str] = None,
    limit: int = 50,
    sort_by: str = "start_time",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """
    Cursor-paginated list of individual time entries.
    TRD v1.3 §6.6 get_detailed.

    Cursor is opaque (base64-encoded entry_id + start_time).
    API Spec v1.1 §14 GET /reports/detailed.
    """
    workspace = await _get_workspace_or_403(db, workspace_id)
    suppress = _is_suppressed(workspace, caller_role)

    # Rule 1 — Member data isolation (PITFALL 1)
    if caller_role in ("member", "viewer"):
        effective_user_id = caller_user_id
        if user_id is not None and user_id != caller_user_id:
            raise HTTPException(
                status_code=403,
                detail="Members can only view their own data",
                headers={"code": "FORBIDDEN"},
            )
    else:
        effective_user_id = user_id

    tz_name = workspace.default_timezone or "UTC"
    start_utc, end_utc = _date_range_utc_bounds(date_from, date_to, tz_name)

    limit = max(1, min(limit, 200))  # clamp 1–200

    stmt = (
        select(TimeEntry)
        .options(
            selectinload(TimeEntry.user),
            selectinload(TimeEntry.project).selectinload(Project.client),
            selectinload(TimeEntry.task),
            selectinload(TimeEntry.tags).selectinload(TimeEntryTag.tag),
        )
        .where(
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.start_time >= start_utc,
            TimeEntry.start_time <= end_utc,
            TimeEntry.duration_seconds.isnot(None),
        )
    )

    if effective_user_id is not None:
        stmt = stmt.where(TimeEntry.user_id == effective_user_id)
    if project_id is not None:
        stmt = stmt.where(TimeEntry.project_id == project_id)
    if task_id is not None:
        stmt = stmt.where(TimeEntry.task_id == task_id)
    if billable is not None:
        stmt = stmt.where(TimeEntry.billable == billable)
    if status is not None:
        stmt = stmt.where(TimeEntry.status == status)
    if tag_ids:
        # Entry must have ALL specified tags (AND semantics)
        for tid in tag_ids:
            stmt = stmt.where(
                TimeEntry.id.in_(
                    select(TimeEntryTag.time_entry_id).where(TimeEntryTag.tag_id == tid)
                )
            )
    if client_id is not None:
        stmt = stmt.join(Project, TimeEntry.project_id == Project.id).where(
            Project.client_id == client_id
        )

    # Parse cursor as page number (default to 1)
    page = 1
    if cursor is not None:
        try:
            page = int(cursor)
            if page < 1: page = 1
        except ValueError:
            pass

    # Ordering
    if sort_by == "duration":
        sort_col = TimeEntry.duration_seconds
    elif sort_by == "project":
        # Project might already be joined if client_id was present, but outerjoin is safer for sorting
        if client_id is None:
            stmt = stmt.outerjoin(Project, TimeEntry.project_id == Project.id)
        sort_col = Project.name
    elif sort_by == "amount":
        sort_col = TimeEntry.billable_amount_cents
    else:
        sort_col = TimeEntry.start_time

    if sort_order.lower() == "asc":
        stmt = stmt.order_by(sort_col.asc(), TimeEntry.id.asc())
    else:
        stmt = stmt.order_by(sort_col.desc(), TimeEntry.id.desc())

    # Pagination
    stmt = stmt.offset((page - 1) * limit).limit(limit + 1)  # fetch one extra to determine next_cursor

    result = await db.execute(stmt)
    entries = result.scalars().all()

    has_next = len(entries) > limit
    if has_next:
        entries = entries[:limit]

    next_cursor = None
    if has_next and entries:
        next_cursor = str(page + 1)

    data = []
    total_seconds = 0
    total_billable_cents = 0

    for entry in entries:
        dur = entry.duration_seconds or 0
        total_seconds += dur
        if entry.billable and entry.billable_amount_cents:
            total_billable_cents += entry.billable_amount_cents

        tags_out = []
        for tet in (entry.tags or []):
            if tet.tag:
                tags_out.append({"id": tet.tag.id, "name": tet.tag.name})

        project_name = entry.project.name if entry.project else None
        client_id_val = entry.project.client_id if entry.project else None
        client_name = (entry.project.client.name
                       if entry.project and entry.project.client else None)
        task_name = entry.task.name if entry.task else None
        user_name = entry.user.full_name if entry.user else "Unknown"

        base = {
            "id": entry.id,
            "user_id": entry.user_id,
            "user_name": user_name,
            "project_id": entry.project_id,
            "project_name": project_name,
            "client_id": client_id_val,
            "client_name": client_name,
            "task_id": entry.task_id,
            "task_name": task_name,
            "description": entry.description,
            "billable": entry.billable,
            "status": entry.status,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "duration_seconds": entry.duration_seconds,
            "tags": tags_out,
        }

        if not suppress:
            base["hourly_rate_cents"] = entry.hourly_rate_cents
            base["billable_amount_cents"] = entry.billable_amount_cents

        data.append(base)

    if suppress:
        summary = {"total_hours": _seconds_to_hours(total_seconds)}
    else:
        summary = {
            "total_hours": _seconds_to_hours(total_seconds),
            "total_billable_amount": _cents_to_decimal_str(total_billable_cents),
        }

    return {
        "data": data,
        "next_cursor": next_cursor,
        "limit": limit,
        "summary": summary,
        "suppress": suppress,
    }


# ── Weekly Report ───────────────────────────────────────────────────────────────

async def get_weekly_report(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_role: str,
    caller_user_id: uuid.UUID,
    date_from: date,
    date_to: date,
    user_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
    billable: Optional[bool] = None,
) -> dict[str, Any]:
    """
    Per-user, per-day breakdown of hours.
    TRD v1.3 §6.6 get_weekly_report (NEW v1.2).

    Authorization (API Spec v1.1 §14):
      - Admin/Manager: see all workspace members' rows
      - Member/Viewer: auto-locked to own user_id;
        supplying another user_id returns 403

    Date span validation: max 31 days (API Spec v1.1 §14).
    Zero-hour days included in response with total_seconds=0.
    """
    workspace = await _get_workspace_or_403(db, workspace_id)
    suppress = _is_suppressed(workspace, caller_role)

    # Validate span ≤ 31 days (API Spec v1.1 §14 / TRD §6.6)
    span_days = (date_to - date_from).days
    if span_days < 0:
        raise HTTPException(
            status_code=400,
            detail="date_to must be >= date_from",
            headers={"code": "BAD_REQUEST"},
        )
    if span_days > 31:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 31 days",
            headers={"code": "BAD_REQUEST"},
        )

    # Rule 1 — Member/Viewer data isolation (TRD §6.6 step 1, PITFALL 1)
    if caller_role in ("member", "viewer"):
        effective_user_id = caller_user_id
        if user_id is not None and user_id != caller_user_id:
            raise HTTPException(
                status_code=403,
                detail="Members and Viewers can only view their own row",
                headers={"code": "FORBIDDEN"},
            )
    else:
        effective_user_id = user_id  # None = all members

    tz_name = workspace.default_timezone or "UTC"
    start_utc, end_utc = _date_range_utc_bounds(date_from, date_to, tz_name)

    # TRD §6.6 step 2 — build list of all calendar days in range
    all_days: list[date] = []
    current_day = date_from
    while current_day <= date_to:
        all_days.append(current_day)
        current_day += timedelta(days=1)

    day_strings = [d.isoformat() for d in all_days]

    # Fetch all workspace members to build full user list (or single user)
    member_stmt = (
        select(WorkspaceMember)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .options(selectinload(WorkspaceMember.user))
    )
    if effective_user_id is not None:
        member_stmt = member_stmt.where(WorkspaceMember.user_id == effective_user_id)

    members_result = await db.execute(member_stmt)
    members = members_result.scalars().all()

    # TRD §6.6 step 3 — GROUP BY (user_id, local_date) aggregating sums
    # Use AT TIME ZONE to convert start_time (UTC) into workspace local date
    local_date_expr = func.date(
        func.timezone(tz_name, TimeEntry.start_time)
    ).label("local_date")

    sum_total = func.coalesce(func.sum(TimeEntry.duration_seconds), 0).label("total_seconds")
    sum_billable = func.coalesce(
        func.sum(
            case((TimeEntry.billable == True, TimeEntry.duration_seconds), else_=0)  # noqa: E712
        ),
        0,
    ).label("billable_seconds")
    sum_billable_amount = func.coalesce(
        func.sum(
            case((TimeEntry.billable == True, TimeEntry.billable_amount_cents), else_=0)  # noqa: E712
        ),
        0,
    ).label("billable_amount_cents")
    count_entries = func.count(TimeEntry.id).label("entry_count")

    agg_stmt = (
        select(
            TimeEntry.user_id,
            local_date_expr,
            sum_total,
            sum_billable,
            sum_billable_amount,
            count_entries,
        )
        .where(
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.start_time >= start_utc,
            TimeEntry.start_time <= end_utc,
            TimeEntry.duration_seconds.isnot(None),
        )
        .group_by(TimeEntry.user_id, local_date_expr)
    )

    if effective_user_id is not None:
        agg_stmt = agg_stmt.where(TimeEntry.user_id == effective_user_id)
    if project_id is not None:
        agg_stmt = agg_stmt.where(TimeEntry.project_id == project_id)
    if billable is not None:
        agg_stmt = agg_stmt.where(TimeEntry.billable == billable)

    agg_result = await db.execute(agg_stmt)
    agg_rows = agg_result.fetchall()

    # TRD §6.6 step 4 — Build per-user, per-day dict
    # Structure: {user_id: {day_str: {total_seconds, billable_seconds, billable_amount_cents, entry_count}}}
    user_day_map: dict[uuid.UUID, dict[str, dict]] = {}
    for row in agg_rows:
        uid = row.user_id
        day_str = row.local_date.isoformat() if hasattr(row.local_date, "isoformat") else str(row.local_date)
        if uid not in user_day_map:
            user_day_map[uid] = {}
        user_day_map[uid][day_str] = {
            "total_seconds": int(row.total_seconds),
            "billable_seconds": int(row.billable_seconds),
            "billable_amount_cents": int(row.billable_amount_cents),
            "entry_count": int(row.entry_count),
        }

    # TRD §6.6 step 5 — Apply Viewer data isolation and assemble response rows
    rows_out = []
    totals_by_day: dict[str, dict] = {d: {"total_seconds": 0, "billable_seconds": 0, "billable_amount_cents": 0} for d in day_strings}
    grand_total_seconds = 0
    grand_total_billable_cents = 0

    for mem in members:
        user_obj = mem.user
        user_name = user_obj.full_name if user_obj else "Unknown"
        avatar_url = getattr(user_obj, "avatar_url", None)

        uid = mem.user_id
        days_data = user_day_map.get(uid, {})

        row_total_seconds = 0
        row_billable_seconds = 0
        row_billable_cents = 0
        days_out: dict = {}

        for day_str in day_strings:
            cell = days_data.get(day_str, {
                "total_seconds": 0,
                "billable_seconds": 0,
                "billable_amount_cents": 0,
                "entry_count": 0,
            })
            t_sec = cell["total_seconds"]
            b_sec = cell["billable_seconds"]
            b_cents = cell["billable_amount_cents"]
            e_count = cell["entry_count"]

            row_total_seconds += t_sec
            row_billable_seconds += b_sec
            row_billable_cents += b_cents

            totals_by_day[day_str]["total_seconds"] += t_sec
            totals_by_day[day_str]["billable_seconds"] += b_sec
            totals_by_day[day_str]["billable_amount_cents"] += b_cents

            if suppress:
                days_out[day_str] = {
                    "total_seconds": t_sec,
                    "total_hours": _seconds_to_hours(t_sec),
                    "entry_count": e_count,
                }
            else:
                days_out[day_str] = {
                    "total_seconds": t_sec,
                    "total_hours": _seconds_to_hours(t_sec),
                    "billable_hours": _seconds_to_hours(b_sec),
                    "billable_amount": _cents_to_decimal_str(b_cents),
                    "entry_count": e_count,
                }

        grand_total_seconds += row_total_seconds
        grand_total_billable_cents += row_billable_cents

        user_row: dict = {
            "user_id": uid,
            "user_name": user_name,
            "avatar_url": avatar_url,
            "total_seconds": row_total_seconds,
            "total_hours": _seconds_to_hours(row_total_seconds),
            "days": days_out,
        }
        if not suppress:
            user_row["billable_hours"] = _seconds_to_hours(row_billable_seconds)
            user_row["total_billable_amount"] = _cents_to_decimal_str(row_billable_cents)

        rows_out.append(user_row)

    # Build totals block
    by_day_out: dict = {}
    for d in day_strings:
        day_stats = {"total_hours": _seconds_to_hours(totals_by_day[d]["total_seconds"])}
        if not suppress:
            day_stats["billable_hours"] = _seconds_to_hours(totals_by_day[d]["billable_seconds"])
            day_stats["billable_amount"] = _cents_to_decimal_str(totals_by_day[d]["billable_amount_cents"])
        by_day_out[d] = day_stats

    totals: dict = {
        "by_day": by_day_out,
        "grand_total_hours": _seconds_to_hours(grand_total_seconds),
    }
    if not suppress:
        totals["grand_total_billable_hours"] = _seconds_to_hours(sum(td["billable_seconds"] for td in totals_by_day.values()))
        totals["grand_total_billable_amount"] = _cents_to_decimal_str(grand_total_billable_cents)

    return {
        "data": {
            "date_from": date_from,
            "date_to": date_to,
            "days": day_strings,
            "rows": rows_out,
            "totals": totals,
        },
        "suppress": suppress,
    }


# ── Saved Views ─────────────────────────────────────────────────────────────────

async def list_saved_views(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[SavedReportView]:
    """
    List saved views for current user in workspace.
    PRD §3.8: "private to their account".
    API Spec v1.1 §14 GET /reports/saved-views.
    """
    result = await db.execute(
        select(SavedReportView)
        .where(
            SavedReportView.workspace_id == workspace_id,
            SavedReportView.user_id == user_id,
        )
        .order_by(SavedReportView.created_at.desc())
    )
    return list(result.scalars().all())


async def create_saved_view(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    report_type: str,
    filters: dict,
) -> SavedReportView:
    """
    Save a filter configuration.
    API Spec v1.1 §14 POST /reports/saved-views.
    Raises 409 DUPLICATE_NAME if user already has a view with this name.

    report_type CHECK: 'summary' | 'detailed' | 'weekly'
    — DB Schema v2.1 §5 (migration 0002).
    Enforced by DB CHECK constraint; caught and re-raised as 409.
    """
    from sqlalchemy.exc import IntegrityError

    # Explicit UNIQUE check before insert to return clean 409
    existing = await db.execute(
        select(SavedReportView).where(
            SavedReportView.workspace_id == workspace_id,
            SavedReportView.user_id == user_id,
            SavedReportView.name == name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A saved view named {name!r} already exists",
            headers={"code": "DUPLICATE_NAME"},
        )

    view = SavedReportView(
        workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        report_type=report_type,
        filters=filters,
    )
    db.add(view)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A saved view with this name already exists",
            headers={"code": "DUPLICATE_NAME"},
        ) from exc
    return view


async def delete_saved_view(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    view_id: uuid.UUID,
) -> None:
    """
    Delete a saved view.
    Verifies ownership — a user can only delete their own views.
    API Spec v1.1 §14 DELETE /reports/saved-views/{view_id}.
    Raises 404 NOT_FOUND if view doesn't exist or belongs to another user.
    """
    view = await db.get(SavedReportView, view_id)
    if not view or view.workspace_id != workspace_id or view.user_id != user_id:
        raise HTTPException(
            status_code=404,
            detail="Saved view not found",
            headers={"code": "NOT_FOUND"},
        )
    await db.delete(view)
    await db.flush()


# ── CSV Export Functions ────────────────────────────────────────────────────────
# PITFALL 4: CSV exports apply EXACTLY the same field suppression as JSON.
# Never bypass the service layer for CSV generation.

async def export_summary_csv(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_role: str,
    caller_user_id: uuid.UUID,
    group_by: Literal["project", "user", "client", "tag"],
    date_from: date,
    date_to: date,
    project_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    billable: Optional[bool] = None,
    status: Optional[str] = None,
) -> StreamingResponse:
    """
    CSV download of Summary report.
    API Spec v1.1 §14 GET /reports/summary/export.
    Viewer / non-billable workspace: financial columns absent (PITFALL 4).

    Columns (full): Group,Total Hours,Billable Hours,Non-Billable Hours,Billable Amount,Entry Count
    Columns (viewer/non-billable): Group,Total Hours,Non-Billable Hours,Entry Count
    """
    payload = await get_summary(
        db=db, workspace_id=workspace_id, caller_role=caller_role,
        caller_user_id=caller_user_id, group_by=group_by,
        date_from=date_from, date_to=date_to,
        project_id=project_id,
        client_id=client_id,
        user_id=user_id, billable=billable, status=status,
    )

    suppress = payload["suppress"]
    data = payload["data"]

    output = io.StringIO()
    writer = csv.writer(output)

    if suppress:
        writer.writerow(["Group", "Total Hours", "Non-Billable Hours", "Entry Count"])
        for row in data:
            writer.writerow([
                row.get("group_label") or "",
                row["total_hours"],
                row["non_billable_hours"],
                row["entry_count"],
            ])
    else:
        writer.writerow(["Group", "Total Hours", "Billable Hours", "Non-Billable Hours", "Billable Amount", "Entry Count"])
        for row in data:
            writer.writerow([
                row.get("group_label") or "",
                row["total_hours"],
                row.get("billable_hours", 0),
                row["non_billable_hours"],
                row.get("total_billable_amount") or "0.00",
                row["entry_count"],
            ])

    csv_bytes = output.getvalue().encode("utf-8")
    filename = f"yusitime_summary_{date_from}_{date_to}.csv"

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def export_detailed_csv(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_role: str,
    caller_user_id: uuid.UUID,
    date_from: date,
    date_to: date,
    project_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    task_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    billable: Optional[bool] = None,
    status: Optional[str] = None,
    tag_ids: Optional[list[uuid.UUID]] = None,
) -> StreamingResponse:
    """
    CSV download of Detailed report.
    API Spec v1.1 §14 GET /reports/detailed/export.
    All entries fetched (limit=10000, no cursor) for export.

    Viewer / non-billable: Billable, Hourly Rate, Billable Amount columns absent.
    Columns: Date,User,Project,Client,Task,Description,Start Time,End Time,Duration (h),Billable,Hourly Rate,Billable Amount,Tags,Status
    """
    payload = await get_detailed(
        db=db, workspace_id=workspace_id, caller_role=caller_role,
        caller_user_id=caller_user_id, date_from=date_from, date_to=date_to,
        project_id=project_id, client_id=client_id, task_id=task_id, user_id=user_id,
        billable=billable, status=status, tag_ids=tag_ids,
        cursor=None, limit=10000,
    )
    workspace = await _get_workspace_or_403(db, workspace_id)
    currency = workspace.currency or "USD"

    suppress = payload["suppress"]
    data = payload["data"]

    output = io.StringIO()
    writer = csv.writer(output)

    if suppress:
        writer.writerow(["Date", "Member", "Project", "Task", "Description", "Duration"])
        for row in data:
            dur_h = round((row["duration_seconds"] or 0) / 3600, 4)
            date_str = row["start_time"].strftime("%m/%d/%Y") if row["start_time"] else ""
            writer.writerow([
                date_str,
                row["user_name"],
                row.get("project_name") or "",
                row.get("task_name") or "",
                row.get("description") or "",
                f"{dur_h:.2f}",
            ])
    else:
        writer.writerow(["Date", "Member", "Project", "Task", "Description", "Duration", "Billable", "Amount", "Currency"])
        for row in data:
            dur_h = round((row["duration_seconds"] or 0) / 3600, 4)
            amount_str = _cents_to_decimal_str(row.get("billable_amount_cents")) or ""
            date_str = row["start_time"].strftime("%m/%d/%Y") if row["start_time"] else ""
            writer.writerow([
                date_str,
                row["user_name"],
                row.get("project_name") or "",
                row.get("task_name") or "",
                row.get("description") or "",
                f"{dur_h:.2f}",
                "Yes" if row["billable"] else "No",
                amount_str,
                currency if amount_str else "",
            ])

    csv_bytes = output.getvalue().encode("utf-8")
    filename = f"yusitime_detailed_{date_from}_{date_to}.csv"

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def export_weekly_csv(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_role: str,
    caller_user_id: uuid.UUID,
    date_from: date,
    date_to: date,
    user_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
    billable: Optional[bool] = None,
) -> StreamingResponse:
    """
    CSV download of Weekly report.
    API Spec v1.1 §14 GET /reports/weekly/export.
    One row per member. Hours as decimal.

    Columns (full): Member, [day headers], Total Hours, Billable Amount
    Columns (viewer/non-billable): Member, [day headers], Total Hours
    """
    payload = await get_weekly_report(
        db=db, workspace_id=workspace_id, caller_role=caller_role,
        caller_user_id=caller_user_id, date_from=date_from, date_to=date_to,
        user_id=user_id, project_id=project_id, billable=billable,
    )

    data = payload["data"]
    suppress = payload["suppress"]
    day_strings = data["days"]
    rows = data["rows"]

    output = io.StringIO()
    writer = csv.writer(output)


    # Day header labels: "Mon 18", "Tue 19" etc. from the date string
    day_labels = []
    for ds in day_strings:
        d = date.fromisoformat(ds)
        day_labels.append(f"{d.strftime('%a')} {d.day}" if hasattr(d, "strftime") else ds)

    if suppress:
        writer.writerow(["Member"] + day_labels + ["Total Hours"])
        for row in rows:
            cells = [_seconds_to_hours(row["days"].get(ds, {}).get("total_seconds", 0)) for ds in day_strings]
            writer.writerow([row["user_name"]] + cells + [row["total_hours"]])
    else:
        writer.writerow(["Member"] + day_labels + ["Total Hours", "Billable Amount"])
        for row in rows:
            cells = [_seconds_to_hours(row["days"].get(ds, {}).get("total_seconds", 0)) for ds in day_strings]
            writer.writerow([row["user_name"]] + cells + [row["total_hours"], row.get("total_billable_amount") or "0.00"])

    csv_bytes = output.getvalue().encode("utf-8")
    filename = f"yusitime_weekly_{date_from}_{date_to}.csv"

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
