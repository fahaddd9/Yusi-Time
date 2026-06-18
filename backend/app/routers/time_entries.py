"""
Time Entry Router — API Spec v1.1 §12.

All 10 endpoints:
  GET  /time-entries/current
  POST /time-entries/start
  POST /time-entries/submit       (Phase 4 — bulk submit drafts to pending)
  POST /time-entries/{entry_id}/stop
  POST /time-entries/{entry_id}/continue   (Phase 5 stub)
  POST /time-entries/{entry_id}/duplicate  (Phase 5 stub)
  GET  /time-entries
  POST /time-entries
  GET  /time-entries/{entry_id}
  PATCH /time-entries/{entry_id}
  DELETE /time-entries/{entry_id}

Viewer isolation is enforced by selecting between TimeEntryObject
and TimeEntryObjectViewer at serialisation time (API Spec §1.11).
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user, get_workspace_member, require_role
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.time_entry import (
    CreateManualEntryRequest,
    CreateManualEntryResponse,
    CreateManualEntryResponseViewer,
    GetCurrentTimerResponse,
    GetCurrentTimerResponseViewer,
    ListEntriesResponse,
    ListEntriesResponseViewer,
    RoundingResultSchema,
    StartTimerRequest,
    StopTimerRequest,
    StopTimerResponse,
    StopTimerResponseViewer,
    TagInEntry,
    TimeEntryObject,
    TimeEntryObjectViewer,
    UpdateEntryRequest,
    UpdateEntryResponse,
    UpdateEntryResponseViewer,
)
from app.services import time_entry_service
from app.services.time_entry_service import _build_entry_dict

router = APIRouter(prefix="/time-entries", tags=["Time Entries"])


class SubmitEntriesRequest(BaseModel):
    """POST /time-entries/submit — Phase 4 Submit Week."""
    entry_ids: list[uuid.UUID]


# ─── Serialisation helpers ────────────────────────────────────────────────────

def _serialise(entry_dict: dict, caller_role: str) -> dict:
    """
    Build a TimeEntryObject or TimeEntryObjectViewer based on role.
    Viewer: financial fields are structurally absent from the model (API Spec §1.11).
    """
    if caller_role == "viewer":
        return TimeEntryObjectViewer(**{
            k: v for k, v in entry_dict.items()
            if k not in ("hourly_rate", "billable_amount")
        }).model_dump()
    return TimeEntryObject(**entry_dict).model_dump()


def _rounding_schema(rounding) -> dict:
    return RoundingResultSchema(
        raw_seconds=rounding.raw_seconds,
        rounded_seconds=rounding.rounded_seconds,
        rounding_mode=rounding.rounding_mode.value,
        rounding_interval_minutes=rounding.rounding_interval_minutes,
    ).model_dump()


# ─── GET /time-entries/current ────────────────────────────────────────────────

@router.get("/current")
async def get_current_timer(
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(get_workspace_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Return the currently running timer, or null.
    GET /time-entries/current — API Spec §12.
    """
    result = await time_entry_service.get_current_timer(
        db, current_user.id, workspace_id
    )
    if result is None:
        return {"data": None}

    entry, user, project, task = result
    entry_dict = _build_entry_dict(entry, user, project, task)
    return {"data": _serialise(entry_dict, member.role)}


# ─── POST /time-entries/start ─────────────────────────────────────────────────

@router.post("/start", status_code=201)
async def start_timer(
    body: StartTimerRequest,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Start a new running timer. Member+ only.
    POST /time-entries/start — API Spec §12.
    """
    entry, user, project, task = await time_entry_service.start_timer(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        project_id=body.project_id,
        task_id=body.task_id,
        description=body.description,
        tag_ids=body.tag_ids,
        billable=body.billable,
        force=body.force,
    )
    entry_dict = _build_entry_dict(entry, user, project, task)
    return {"data": _serialise(entry_dict, member.role)}


# ─── POST /time-entries/submit ────────────────────────────────────────────────

@router.post("/submit")
async def submit_entries(
    body: SubmitEntriesRequest,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Bulk-submit draft entries to 'pending' status.
    Only the owner or Admin/Manager may submit each entry.
    POST /time-entries/submit — Phase 4 Submit Week.
    """
    from app.models.time_entry import TimeEntry
    from fastapi import HTTPException

    submitted_ids = []
    for entry_id in body.entry_ids:
        entry = await db.get(TimeEntry, entry_id)
        if not entry or entry.workspace_id != workspace_id:
            continue  # silently skip entries not in this workspace
        if entry.status != "draft":
            continue  # only draft entries can be submitted
        if member.role == "member" and entry.user_id != current_user.id:
            continue  # members can only submit their own
        entry.status = "pending"
        submitted_ids.append(str(entry_id))

    await db.flush()
    return {"submitted": submitted_ids, "count": len(submitted_ids)}


# ─── POST /time-entries/{entry_id}/stop ───────────────────────────────────────

@router.post("/{entry_id}/stop")
async def stop_timer(
    entry_id: uuid.UUID,
    body: StopTimerRequest,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(get_workspace_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Stop a running timer. Applies rounding. Returns entry + rounding result.
    POST /time-entries/{entry_id}/stop — API Spec §12.
    """
    entry, user, project, task, rounding = await time_entry_service.stop_timer(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        entry_id=str(entry_id),
        idle_end_time=body.idle_end_time,
    )
    entry_dict = _build_entry_dict(entry, user, project, task)
    return {
        "data": _serialise(entry_dict, member.role),
        "rounding": _rounding_schema(rounding),
    }


# ─── POST /time-entries/{entry_id}/continue  (Phase 5 stub) ──────────────────

@router.post("/{entry_id}/continue", status_code=201)
async def continue_entry(
    entry_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Phase 5 stub — not yet implemented."""
    await time_entry_service.continue_entry(
        db, current_user.id, workspace_id, member.role, str(entry_id), force=False
    )


# ─── POST /time-entries/{entry_id}/duplicate  (Phase 5 stub) ─────────────────

@router.post("/{entry_id}/duplicate", status_code=201)
async def duplicate_entry(
    entry_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Phase 5 stub — not yet implemented."""
    await time_entry_service.duplicate_entry(
        db, current_user.id, workspace_id, member.role, str(entry_id)
    )


# ─── GET /time-entries ────────────────────────────────────────────────────────

@router.get("")
async def list_entries(
    workspace_id: uuid.UUID = Query(...),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user_id: uuid.UUID | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    billable: bool | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    tag_ids: str | None = Query(None),
    member: WorkspaceMember = Depends(get_workspace_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List time entries (cursor-paginated). Members see own only.
    GET /time-entries — API Spec §12.
    """
    tag_id_list: list[uuid.UUID] = []
    if tag_ids:
        try:
            tag_id_list = [uuid.UUID(t.strip()) for t in tag_ids.split(",") if t.strip()]
        except ValueError:
            pass

    enriched, next_cursor = await time_entry_service.list_entries(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        cursor=cursor,
        limit=limit,
        filter_user_id=user_id,
        project_id=project_id,
        status=status,
        billable=billable,
        date_from=date_from,
        date_to=date_to,
        tag_ids_filter=tag_id_list or None,
    )

    serialised = [
        _serialise(_build_entry_dict(entry, user, project, task), member.role)
        for entry, user, project, task in enriched
    ]

    return {
        "data": serialised,
        "next_cursor": next_cursor,
        "limit": limit,
    }


# ─── POST /time-entries  (manual entry) ───────────────────────────────────────

@router.post("", status_code=201)
async def create_manual_entry(
    body: CreateManualEntryRequest,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a manual (non-timer) time entry.
    POST /time-entries — API Spec §12.
    """
    entry, user, project, task, rounding, has_overlap = await time_entry_service.create_manual_entry(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        project_id=body.project_id,
        task_id=body.task_id,
        start_time=body.start_time,
        end_time=body.end_time,
        description=body.description,
        billable=body.billable,
        tag_ids=body.tag_ids,
    )
    entry_dict = _build_entry_dict(entry, user, project, task)
    return {
        "data": _serialise(entry_dict, member.role),
        "rounding": _rounding_schema(rounding),
        "has_overlap": has_overlap,
    }


# ─── GET /time-entries/{entry_id} ─────────────────────────────────────────────

@router.get("/{entry_id}")
async def get_entry(
    entry_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(get_workspace_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single time entry.
    GET /time-entries/{entry_id} — API Spec §12.
    """
    entry, user, project, task = await time_entry_service.get_entry(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        entry_id=str(entry_id),
    )
    entry_dict = _build_entry_dict(entry, user, project, task)
    return {"data": _serialise(entry_dict, member.role)}


# ─── PATCH /time-entries/{entry_id} ──────────────────────────────────────────

@router.patch("/{entry_id}")
async def update_entry(
    entry_id: uuid.UUID,
    body: UpdateEntryRequest,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(get_workspace_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a time entry (subject to lock rules). Re-rounds and re-snapshots rate.
    PATCH /time-entries/{entry_id} — API Spec §12.
    """
    entry, user, project, task, rounding = await time_entry_service.update_entry(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        entry_id=str(entry_id),
        project_id=body.project_id,
        task_id=body.task_id,
        start_time=body.start_time,
        end_time=body.end_time,
        description=body.description,
        billable=body.billable,
        tag_ids=body.tag_ids,
    )
    entry_dict = _build_entry_dict(entry, user, project, task)
    return {
        "data": _serialise(entry_dict, member.role),
        "rounding": _rounding_schema(rounding),
    }


# ─── DELETE /time-entries/{entry_id} ─────────────────────────────────────────

@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(get_workspace_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a time entry (subject to lock rules).
    DELETE /time-entries/{entry_id} — API Spec §12.
    """
    await time_entry_service.delete_entry(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        caller_role=member.role,
        entry_id=str(entry_id),
    )
    return {"message": "Time entry deleted."}
