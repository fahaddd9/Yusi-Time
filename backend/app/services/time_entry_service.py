"""
Time Entry Service — Implementation Plan §4.5, TRD v1.2 §6.6.

All 7 core functions:
  - start_timer
  - stop_timer
  - create_manual_entry
  - update_entry
  - delete_entry
  - list_entries
  - get_entry

Scaffolded stubs for Phase 5:
  - continue_entry (POST /{id}/continue)
  - duplicate_entry (POST /{id}/duplicate)

Business rules per PRD §5 and TRD §6.6.
Raw seconds are NEVER persisted — only rounded values (PRD §3.3.4).
All saves call rate_service.resolve_rate() for a fresh snapshot.
All saves return RoundingResult so the frontend can show the toast (PRD §7).
"""
from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.time_entry_tag import TimeEntryTag
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.services import rate_service
from app.services.rounding_service import RoundingMode, RoundingResult, RoundingRule, round_duration


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _build_rounding_rule(workspace: Workspace) -> RoundingRule:
    """Convert workspace settings into a RoundingRule dataclass."""
    try:
        mode = RoundingMode(workspace.rounding_mode)
    except ValueError:
        mode = RoundingMode.NONE
    return RoundingRule(mode=mode, interval_minutes=workspace.rounding_interval_minutes)


def _compute_billable_amount(duration_seconds: int, rate_cents: int | None) -> int | None:
    """
    Compute billable_amount_cents from rounded duration and snapshotted rate.
    Implementation Plan §4.5 _compute_billable.
    Returns None when rate_cents is None.
    """
    if rate_cents is None:
        return None
    return round((duration_seconds / 3600.0) * rate_cents)


def _check_lock(entry: TimeEntry, caller_role: str, workspace: Workspace) -> None:
    """
    Enforce entry lock rules. Raises 403 ENTRY_LOCKED if entry cannot be modified.
    Implementation Plan §4.5 _check_lock, PRD §5 Rolling Lock Date.

    Admin role bypasses all locks unconditionally.
    Non-Admins cannot edit:
      - status=pending or status=approved entries
      - entries older than workspace.lock_period_days
    """
    if caller_role == "admin":
        return  # Admin is never locked (PRD §4)

    if entry.status in ("pending", "approved"):
        raise HTTPException(
            status_code=403,
            detail="Entry is locked",
            headers={"code": "ENTRY_LOCKED"},
        )

    if workspace.lock_period_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=workspace.lock_period_days)
        entry_start = entry.start_time
        if entry_start.tzinfo is None:
            entry_start = entry_start.replace(tzinfo=timezone.utc)
        if entry_start < cutoff:
            raise HTTPException(
                status_code=403,
                detail="Entry is past the rolling lock date",
                headers={"code": "ENTRY_LOCKED"},
            )


async def _get_running_timer(
    db: AsyncSession, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> TimeEntry | None:
    """Return the active running timer for this user in this workspace, or None."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == user_id,
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.status == "running",
        )
    )
    return result.scalar_one_or_none()


async def _load_entry_with_tags(db: AsyncSession, entry_id: uuid.UUID) -> TimeEntry | None:
    """Load a TimeEntry and eagerly load its tags relationship."""
    result = await db.execute(
        select(TimeEntry)
        .options(selectinload(TimeEntry.tags).selectinload(TimeEntryTag.tag))
        .where(TimeEntry.id == entry_id)
    )
    return result.scalar_one_or_none()


async def _validate_project_access(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    caller_role: str,
    user_id: uuid.UUID,
) -> Project:
    """
    Ensure the project exists, is active, and the caller can log time on it.
    PRD §4: Members/Viewers can only log time on public projects or assigned private ones.
    """
    project = await db.get(Project, project_id)
    if not project or project.workspace_id != workspace_id or project.status == "archived":
        raise HTTPException(
            status_code=404,
            detail="Project not found or archived",
            headers={"code": "NOT_FOUND"},
        )

    if project.visibility == "private" and caller_role in ("member", "viewer"):
        # Check if the user is assigned to this private project
        pm_result = await db.execute(
            select(WorkspaceMember)  # reuse via project_members
            .where(
                and_(
                    # We join project_members
                )
            )
        )
        from app.models.project_member import ProjectMember
        pm_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        pm = pm_result.scalar_one_or_none()
        if pm is None:
            raise HTTPException(
                status_code=403,
                detail="Access denied to private project",
                headers={"code": "FORBIDDEN"},
            )
    return project


async def _validate_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Task:
    """Ensure task exists and belongs to the project."""
    task = await db.get(Task, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
            headers={"code": "NOT_FOUND"},
        )
    return task


async def _validate_tags(
    db: AsyncSession,
    tag_ids: list[uuid.UUID],
    workspace_id: uuid.UUID,
) -> None:
    """Ensure all tag_ids exist and belong to the workspace."""
    if not tag_ids:
        return
    result = await db.execute(
        select(Tag).where(
            Tag.id.in_(tag_ids),
            Tag.workspace_id == workspace_id,
        )
    )
    found = result.scalars().all()
    if len(found) != len(tag_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more tags not found in workspace",
            headers={"code": "NOT_FOUND"},
        )


async def _attach_tags(db: AsyncSession, entry: TimeEntry, tag_ids: list[uuid.UUID]) -> None:
    """Insert TimeEntryTag junction rows for the given tag_ids."""
    for tag_id in tag_ids:
        db.add(TimeEntryTag(time_entry_id=entry.id, tag_id=tag_id))


async def _replace_tags(
    db: AsyncSession, entry: TimeEntry, tag_ids: list[uuid.UUID]
) -> None:
    """Remove all existing tags from an entry and attach the new set."""
    # Delete existing junction rows
    from sqlalchemy import delete as sa_delete
    await db.execute(
        sa_delete(TimeEntryTag).where(TimeEntryTag.time_entry_id == entry.id)
    )
    await _attach_tags(db, entry, tag_ids)


def _build_cursor(entry: TimeEntry) -> str:
    """Encode (start_time, id) into an opaque cursor string."""
    payload = {
        "st": entry.start_time.isoformat(),
        "id": str(entry.id),
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _parse_cursor(cursor: str) -> tuple[datetime, uuid.UUID] | None:
    """Decode opaque cursor string back to (start_time, id)."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor).decode())
        return datetime.fromisoformat(payload["st"]), uuid.UUID(payload["id"])
    except Exception:
        return None


def _build_entry_dict(entry: TimeEntry, user: User, project: Project, task: Task | None) -> dict:
    """
    Build the raw dict for constructing TimeEntryObject / TimeEntryObjectViewer.
    Denormalizes user_name, project_name, project_color, task_name.
    Financial fields included — router strips them for Viewer via schema selection.
    """
    rate_cents = entry.hourly_rate_cents
    billable_amount_cents = entry.billable_amount_cents

    def cents_to_str(c: int | None) -> str | None:
        if c is None:
            return None
        return f"{c / 100:.2f}"

    tags = [
        {
            "id": jet.tag_id,
            "workspace_id": jet.tag.workspace_id if jet.tag else None,
            "name": jet.tag.name if jet.tag else "",
            "color": jet.tag.color if jet.tag else None,
        }
        for jet in (entry.tags or [])
    ]

    return {
        "id": entry.id,
        "workspace_id": entry.workspace_id,
        "user_id": entry.user_id,
        "user_name": user.full_name,
        "project_id": entry.project_id,
        "project_name": project.name,
        "project_color": project.color,
        "task_id": entry.task_id,
        "task_name": task.name if task else None,
        "description": entry.description,
        "billable": entry.billable,
        "status": entry.status,
        "start_time": entry.start_time,
        "end_time": entry.end_time,
        "duration_seconds": entry.duration_seconds,
        "tags": tags,
        "hourly_rate": cents_to_str(rate_cents),
        "billable_amount": cents_to_str(billable_amount_cents),
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


# ─── Public service functions ─────────────────────────────────────────────────

async def start_timer(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    project_id: uuid.UUID,
    task_id: uuid.UUID | None,
    description: str | None,
    tag_ids: list[uuid.UUID],
    billable: bool | None,
    force: bool,
) -> tuple[TimeEntry, User, Project, Task | None]:
    """
    Start a new running timer for this user.
    TRD §6.6 start_timer, PRD §5 Timer Singleton.

    Returns (entry, user, project, task) — router wraps into TimeEntryObject.
    """
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found", headers={"code": "NOT_FOUND"})

    # Mandatory description check (PRD §5 Business Rules)
    if workspace.mandatory_description and not description:
        raise HTTPException(
            status_code=400,
            detail="Description is required by workspace settings",
            headers={"code": "MANDATORY_DESCRIPTION"},
        )

    # Timer singleton check (PRD §5, TRD §6.6)
    running = await _get_running_timer(db, user_id, workspace_id)
    if running:
        if not force:
            raise HTTPException(
                status_code=409,
                detail="A timer is already running",
                headers={"code": "TIMER_ALREADY_RUNNING"},
            )
        # force=True: stop the running timer first (rounding applied)
        await stop_timer(db, user_id, workspace_id, caller_role, str(running.id), idle_end_time=None)

    # Validate project access
    project = await _validate_project_access(db, workspace_id, project_id, caller_role, user_id)

    # Validate task if provided
    task: Task | None = None
    if task_id:
        task = await _validate_task(db, task_id, project_id)

    # Validate tags
    await _validate_tags(db, tag_ids, workspace_id)

    # Determine billable flag: caller-supplied → project default
    effective_billable = billable if billable is not None else project.default_billable

    # Rate snapshot (PRD §5 Rate Snapshot)
    rate_cents = await rate_service.resolve_rate(db, workspace_id, project_id, task_id)

    # Create the running entry
    entry = TimeEntry(
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=project_id,
        task_id=task_id,
        description=description,
        billable=effective_billable,
        status="running",
        start_time=datetime.now(timezone.utc),
        hourly_rate_cents=rate_cents,
    )
    db.add(entry)
    await db.flush()  # get entry.id

    await _attach_tags(db, entry, tag_ids)

    # Reload entry to eagerly fetch tags for _build_entry_dict
    entry = await _load_entry_with_tags(db, entry.id)

    user = await db.get(User, user_id)
    return entry, user, project, task


async def stop_timer(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    entry_id: str,
    idle_end_time: datetime | None,
) -> tuple[TimeEntry, User, Project, Task | None, RoundingResult]:
    """
    Stop a running timer, apply rounding, persist rounded duration.
    TRD §6.6 stop_timer.

    Returns (entry, user, project, task, rounding_result) — raw seconds are NEVER persisted.
    """
    entry = await _load_entry_with_tags(db, uuid.UUID(entry_id))
    if not entry or entry.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Entry not found", headers={"code": "NOT_FOUND"})

    if entry.status != "running":
        raise HTTPException(
            status_code=400,
            detail="Entry is not a running timer",
            headers={"code": "BAD_REQUEST"},
        )

    # Only owner, Manager, or Admin can stop
    if caller_role == "member" and entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden", headers={"code": "FORBIDDEN"})

    workspace = await db.get(Workspace, workspace_id)

    # Compute raw duration (idle_end_time or now — PRD §3.3.3)
    end_dt = idle_end_time or datetime.now(timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    start_dt = entry.start_time
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    raw_seconds = max(0, int((end_dt - start_dt).total_seconds()))

    # Apply rounding (PRD §5 — raw seconds NEVER stored)
    rule = _build_rounding_rule(workspace)
    rounding_result = round_duration(raw_seconds, rule)

    # Compute billable amount with fresh rate re-snapshot
    rate_cents = await rate_service.resolve_rate(db, workspace_id, entry.project_id, entry.task_id)
    billable_cents = _compute_billable_amount(rounding_result.rounded_seconds, rate_cents)

    # Persist rounded values
    entry.end_time = end_dt
    entry.duration_seconds = rounding_result.rounded_seconds  # ROUNDED, never raw
    entry.status = "draft"
    entry.hourly_rate_cents = rate_cents
    entry.billable_amount_cents = billable_cents

    project = await db.get(Project, entry.project_id)
    task = await db.get(Task, entry.task_id) if entry.task_id else None
    user = await db.get(User, entry.user_id)

    return entry, user, project, task, rounding_result


async def create_manual_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    project_id: uuid.UUID,
    task_id: uuid.UUID | None,
    start_time: datetime,
    end_time: datetime,
    description: str | None,
    billable: bool | None,
    tag_ids: list[uuid.UUID],
) -> tuple[TimeEntry, User, Project, Task | None, RoundingResult, bool]:
    """
    Create a manual (non-timer) time entry.
    TRD §6.6 create_manual_entry.

    Returns (entry, user, project, task, rounding_result, has_overlap).
    has_overlap is a soft warning — entry IS created even when overlap exists (PRD §5).
    """
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found", headers={"code": "NOT_FOUND"})

    # Mandatory description check
    if workspace.mandatory_description and not description:
        raise HTTPException(
            status_code=400,
            detail="Description is required by workspace settings",
            headers={"code": "MANDATORY_DESCRIPTION"},
        )

    # Normalize timezone-aware datetimes
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    # Validate start < end
    if start_time >= end_time:
        raise HTTPException(
            status_code=400,
            detail="start_time must be before end_time",
            headers={"code": "BAD_REQUEST"},
        )

    # Past entry limit (PRD §5, TRD §6.6)
    if workspace.past_entry_limit_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=workspace.past_entry_limit_days)
        if start_time < cutoff:
            raise HTTPException(
                status_code=400,
                detail=f"Entry cannot be backdated more than {workspace.past_entry_limit_days} days",
                headers={"code": "PAST_ENTRY_LIMIT_EXCEEDED"},
            )

    # Validate project and tags
    project = await _validate_project_access(db, workspace_id, project_id, caller_role, user_id)
    task: Task | None = None
    if task_id:
        task = await _validate_task(db, task_id, project_id)
    await _validate_tags(db, tag_ids, workspace_id)

    # Overlap detection — soft warning only (PRD §5)
    overlap_result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == user_id,
            TimeEntry.workspace_id == workspace_id,
            TimeEntry.status != "running",
            TimeEntry.start_time < end_time,
            TimeEntry.end_time > start_time,
        )
    )
    has_overlap = overlap_result.first() is not None

    # Rounding
    raw_seconds = int((end_time - start_time).total_seconds())
    rule = _build_rounding_rule(workspace)
    rounding_result = round_duration(raw_seconds, rule)

    # Rate snapshot
    rate_cents = await rate_service.resolve_rate(db, workspace_id, project_id, task_id)
    billable_cents = _compute_billable_amount(rounding_result.rounded_seconds, rate_cents)

    effective_billable = billable if billable is not None else project.default_billable

    entry = TimeEntry(
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=project_id,
        task_id=task_id,
        description=description,
        billable=effective_billable,
        status="draft",
        start_time=start_time,
        end_time=end_time,
        duration_seconds=rounding_result.rounded_seconds,
        hourly_rate_cents=rate_cents,
        billable_amount_cents=billable_cents,
    )
    db.add(entry)
    await db.flush()
    await _attach_tags(db, entry, tag_ids)

    # Reload entry to eagerly fetch tags for _build_entry_dict
    entry = await _load_entry_with_tags(db, entry.id)

    user = await db.get(User, user_id)
    return entry, user, project, task, rounding_result, has_overlap


async def update_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    entry_id: str,
    project_id: uuid.UUID | None,
    task_id: uuid.UUID | None,
    start_time: datetime | None,
    end_time: datetime | None,
    description: str | None,
    billable: bool | None,
    tag_ids: list[uuid.UUID] | None,
) -> tuple[TimeEntry, User, Project, Task | None, RoundingResult]:
    """
    Update a time entry. Re-rounds from new raw duration and re-snapshots rate.
    TRD §6.6 update_entry, PRD §5 Rounding.
    """
    entry = await _load_entry_with_tags(db, uuid.UUID(entry_id))
    if not entry or entry.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Entry not found", headers={"code": "NOT_FOUND"})

    # Members can only edit own entries
    if caller_role == "member" and entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden", headers={"code": "FORBIDDEN"})

    workspace = await db.get(Workspace, workspace_id)
    _check_lock(entry, caller_role, workspace)

    # Apply updates
    if project_id is not None:
        project = await _validate_project_access(db, workspace_id, project_id, caller_role, user_id)
        entry.project_id = project_id
    else:
        project = await db.get(Project, entry.project_id)

    if task_id is not None:
        task = await _validate_task(db, task_id, entry.project_id)
        entry.task_id = task_id
    elif task_id is None and "task_id" in ({}):
        entry.task_id = None
        task = None
    else:
        task = await db.get(Task, entry.task_id) if entry.task_id else None

    if start_time is not None:
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        entry.start_time = start_time

    if end_time is not None:
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        entry.end_time = end_time

    if description is not None:
        entry.description = description

    if billable is not None:
        entry.billable = billable

    # Validate start < end after applying updates
    if entry.start_time and entry.end_time:
        st = entry.start_time
        et = entry.end_time
        if st.tzinfo is None:
            st = st.replace(tzinfo=timezone.utc)
        if et.tzinfo is None:
            et = et.replace(tzinfo=timezone.utc)
        if st >= et:
            raise HTTPException(
                status_code=400,
                detail="start_time must be before end_time",
                headers={"code": "BAD_REQUEST"},
            )
        raw_seconds = int((et - st).total_seconds())
    else:
        raw_seconds = entry.duration_seconds or 0

    # Re-round from new raw value (PRD §3.3.7 — re-rounds from newly submitted value)
    rule = _build_rounding_rule(workspace)
    rounding_result = round_duration(raw_seconds, rule)
    entry.duration_seconds = rounding_result.rounded_seconds

    # Re-snapshot rate from current hierarchy (TRD §6.6 update_entry)
    rate_cents = await rate_service.resolve_rate(db, workspace_id, entry.project_id, entry.task_id)
    entry.hourly_rate_cents = rate_cents
    entry.billable_amount_cents = _compute_billable_amount(rounding_result.rounded_seconds, rate_cents)

    # Replace tags if provided
    if tag_ids is not None:
        await _validate_tags(db, tag_ids, workspace_id)
        await _replace_tags(db, entry, tag_ids)
        
    # Always reload after updates to ensure relations like tags are fresh
    entry = await _load_entry_with_tags(db, entry.id)

    user = await db.get(User, entry.user_id)
    return entry, user, project, task, rounding_result


async def delete_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    entry_id: str,
) -> None:
    """
    Hard-delete a time entry. Same lock rules as update_entry.
    TRD §6.6 delete_entry.
    """
    entry = await db.get(TimeEntry, uuid.UUID(entry_id))
    if not entry or entry.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Entry not found", headers={"code": "NOT_FOUND"})

    if caller_role == "member" and entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden", headers={"code": "FORBIDDEN"})

    workspace = await db.get(Workspace, workspace_id)
    _check_lock(entry, caller_role, workspace)

    await db.delete(entry)


async def get_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    entry_id: str,
) -> tuple[TimeEntry, User, Project, Task | None]:
    """
    Fetch a single time entry. Members see own only; Managers/Admins see any.
    """
    entry = await _load_entry_with_tags(db, uuid.UUID(entry_id))
    if not entry or entry.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Entry not found", headers={"code": "NOT_FOUND"})

    if caller_role == "member" and entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden", headers={"code": "FORBIDDEN"})

    user = await db.get(User, entry.user_id)
    project = await db.get(Project, entry.project_id)
    task = await db.get(Task, entry.task_id) if entry.task_id else None
    return entry, user, project, task


async def get_current_timer(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> tuple[TimeEntry, User, Project, Task | None] | None:
    """
    Return the running timer for this user+workspace, or None.
    GET /time-entries/current — API Spec §12.
    """
    entry = await _get_running_timer(db, user_id, workspace_id)
    if entry is None:
        return None

    # Reload with tags
    entry = await _load_entry_with_tags(db, entry.id)
    user = await db.get(User, entry.user_id)
    project = await db.get(Project, entry.project_id)
    task = await db.get(Task, entry.task_id) if entry.task_id else None
    return entry, user, project, task


async def list_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    cursor: str | None,
    limit: int,
    filter_user_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
    status: str | None,
    billable: bool | None,
    date_from: str | None,
    date_to: str | None,
    tag_ids_filter: list[uuid.UUID] | None,
) -> tuple[list[tuple[TimeEntry, User, Project, Task | None]], str | None]:
    """
    Cursor-paginated list of time entries. API Spec §12 GET /time-entries.
    Members are locked to their own entries regardless of filter_user_id.
    Cursor encodes (start_time DESC, id DESC).
    """
    query = (
        select(TimeEntry)
        .options(selectinload(TimeEntry.tags).selectinload(TimeEntryTag.tag))
        .where(TimeEntry.workspace_id == workspace_id)
        .order_by(TimeEntry.start_time.desc(), TimeEntry.id.desc())
    )

    # Authorization: Members see only own entries (PRD §4)
    if caller_role in ("member", "viewer"):
        query = query.where(TimeEntry.user_id == user_id)
    elif filter_user_id:
        query = query.where(TimeEntry.user_id == filter_user_id)

    if project_id:
        query = query.where(TimeEntry.project_id == project_id)
    if status:
        query = query.where(TimeEntry.status == status)
    if billable is not None:
        query = query.where(TimeEntry.billable == billable)
    # Fetch workspace timezone for date filtering
    from app.models.workspace import Workspace
    import zoneinfo
    
    workspace = await db.get(Workspace, workspace_id)
    tz_name = workspace.default_timezone if workspace and workspace.default_timezone else "UTC"
    if tz_name == "UTC":
        tz = timezone.utc
    else:
        tz = zoneinfo.ZoneInfo(tz_name)

    if date_from:
        df = datetime.fromisoformat(date_from)
        df = datetime.combine(df.date(), df.time(), tzinfo=tz)
        df_utc = df.astimezone(timezone.utc)
        query = query.where(TimeEntry.start_time >= df_utc)
    if date_to:
        dt = datetime.fromisoformat(date_to)
        dt = datetime.combine(dt.date(), dt.time(), tzinfo=tz)
        # Include the whole day
        dt = dt + timedelta(days=1)
        dt_utc = dt.astimezone(timezone.utc)
        query = query.where(TimeEntry.start_time < dt_utc)

    # Cursor-based pagination
    if cursor:
        parsed = _parse_cursor(cursor)
        if parsed:
            cursor_start, cursor_id = parsed
            query = query.where(
                (TimeEntry.start_time < cursor_start)
                | (
                    (TimeEntry.start_time == cursor_start)
                    & (TimeEntry.id < cursor_id)
                )
            )

    query = query.limit(limit + 1)
    result = await db.execute(query)
    entries = list(result.scalars().all())

    has_more = len(entries) > limit
    if has_more:
        entries = entries[:limit]

    next_cursor = _build_cursor(entries[-1]) if has_more and entries else None

    # Enrich with related objects
    enriched: list[tuple[TimeEntry, User, Project, Task | None]] = []
    for entry in entries:
        user = await db.get(User, entry.user_id)
        project = await db.get(Project, entry.project_id)
        task = await db.get(Task, entry.task_id) if entry.task_id else None
        enriched.append((entry, user, project, task))

    return enriched, next_cursor


# ─── Phase 5 stubs (scaffolded per Implementation Plan §4.6) ─────────────────

async def continue_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    entry_id: str,
    force: bool,
) -> tuple[TimeEntry, User, Project, Task | None]:
    """
    POST /{entry_id}/continue — implemented in Phase 5.
    TRD §6.6 continue_entry.
    """
    source = await _load_entry_with_tags(db, uuid.UUID(entry_id))
    if not source or source.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Entry not found", headers={"code": "NOT_FOUND"})

    # Authorization
    if caller_role == "member" and source.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot continue another user's entry",
            headers={"code": "FORBIDDEN"},
        )

    # Status check
    if source.status == "pending":
        raise HTTPException(
            status_code=400,
            detail="Cannot continue a pending entry",
            headers={"code": "CANNOT_CONTINUE_PENDING"},
        )

    # Timer conflict
    running = await _get_running_timer(db, user_id, workspace_id)
    if running:
        if not force:
            raise HTTPException(
                status_code=409,
                detail="Timer already running",
                headers={"code": "TIMER_ALREADY_RUNNING"},
            )
        # force=True: stop the running timer first
        await stop_timer(db, user_id, workspace_id, caller_role, str(running.id), idle_end_time=None)

    # Copy tags from source
    tag_ids = [row.tag_id for row in (source.tags or [])]

    # Fresh rate snapshot
    rate_cents = await rate_service.resolve_rate(db, workspace_id, source.project_id, source.task_id)

    # Create new entry
    new_entry = TimeEntry(
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=source.project_id,
        task_id=source.task_id,
        description=source.description,
        billable=source.billable,
        status="running",
        start_time=datetime.now(timezone.utc),
        hourly_rate_cents=rate_cents,
    )
    db.add(new_entry)
    await db.flush()

    await _attach_tags(db, new_entry, tag_ids)

    # Reload entry to eagerly fetch tags
    new_entry = await _load_entry_with_tags(db, new_entry.id)

    user = await db.get(User, user_id)
    project = await db.get(Project, new_entry.project_id)
    task = await db.get(Task, new_entry.task_id) if new_entry.task_id else None

    return new_entry, user, project, task


async def duplicate_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    caller_role: str,
    entry_id: str,
) -> tuple[TimeEntry, User, Project, Task | None, RoundingResult]:
    """
    POST /{entry_id}/duplicate — implemented in Phase 5.
    TRD §6.6 duplicate_entry.
    """
    source = await _load_entry_with_tags(db, uuid.UUID(entry_id))
    if not source or source.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Entry not found", headers={"code": "NOT_FOUND"})

    if caller_role == "member" and source.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot duplicate another user's entry",
            headers={"code": "FORBIDDEN"},
        )

    if source.status == "pending":
        raise HTTPException(
            status_code=400,
            detail="Cannot duplicate a pending entry",
            headers={"code": "CANNOT_DUPLICATE_PENDING"},
        )

    raw_seconds = source.duration_seconds or 0
    if source.start_time and source.end_time and raw_seconds == 0:
        raw_seconds = int((source.end_time - source.start_time).total_seconds())

    workspace = await db.get(Workspace, workspace_id)
    rule = _build_rounding_rule(workspace)
    rounding_result = round_duration(raw_seconds, rule)

    rate_cents = await rate_service.resolve_rate(db, workspace_id, source.project_id, source.task_id)
    billable_cents = _compute_billable_amount(rounding_result.rounded_seconds, rate_cents)

    now = datetime.now(timezone.utc)
    start_time = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    end_time = start_time + timedelta(seconds=raw_seconds)

    new_entry = TimeEntry(
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=source.project_id,
        task_id=source.task_id,
        description=source.description,
        billable=source.billable,
        status="draft",
        start_time=start_time,
        end_time=end_time,
        duration_seconds=rounding_result.rounded_seconds,
        hourly_rate_cents=rate_cents,
        billable_amount_cents=billable_cents,
    )
    db.add(new_entry)
    await db.flush()

    tag_ids = [row.tag_id for row in (source.tags or [])]
    await _attach_tags(db, new_entry, tag_ids)

    # Reload entry to eagerly fetch tags
    new_entry = await _load_entry_with_tags(db, new_entry.id)

    user = await db.get(User, user_id)
    project = await db.get(Project, new_entry.project_id)
    task = await db.get(Task, new_entry.task_id) if new_entry.task_id else None

    return new_entry, user, project, task, rounding_result
