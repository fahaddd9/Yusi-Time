"""
Rate service — Implementation Plan §4.3, TRD v1.2 §6.6.
Phase 6.5 Addendum §2.4, PRD-ADD-05: is_billable short-circuit added.

Resolves the effective hourly rate for a time entry using the 4-level hierarchy:
  1. Task-level rate (highest priority)
  2. Project-level rate
  3. Client-level rate
  4. Workspace default rate (lowest priority)
  5. None if no rate is defined at any level

Phase 6.5 addition (PRD-ADD-05):
  When workspace.is_billable = False, the entire hierarchy short-circuits
  to None immediately — no rate is applied to any new entry in that workspace.
  Existing stored rate data (hourly_rate_cents on tasks/projects/clients/workspace)
  is NEVER deleted or modified by this toggle (PRD-ADD-05, PRD-ADD-06).
  Existing time entries that already have a billable_amount_cents snapshot
  retain that value unchanged (Rate Snapshot Rules: "once saved, rate never
  changes on an existing entry" — consistent with existing TRD behavior).

Called on EVERY time entry save: stop_timer, create_manual_entry, update_entry,
continue_entry (Phase 5), duplicate_entry (Phase 5).
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project
from app.models.client import Client
from app.models.workspace import Workspace


async def resolve_rate(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID | None,
) -> int | None:
    """
    Return the effective hourly rate in cents, or None if no rate is defined.

    Phase 6.5 addition — PRD-ADD-05 (Addendum §2.4):
      Short-circuits to None immediately if workspace.is_billable = False.
      This preserves all stored rate data without touching it.

    Rate hierarchy (PRD §5 Rate Snapshot, Implementation Plan §4.3):
      1. Task.hourly_rate_cents  — if task_id is provided and task has a rate
      2. Project.hourly_rate_cents — if project has a rate
      3. Client.hourly_rate_cents — if project has a client and client has a rate
      4. Workspace.default_hourly_rate_cents — workspace default

    The result is snapshotted onto the time entry at creation/edit time.
    Subsequent rate changes do NOT affect already-saved entries.
    """
    # Phase 6.5 — PRD-ADD-05: is_billable short-circuit
    # Fetch workspace first; short-circuit entire hierarchy if not billable.
    workspace = await db.get(Workspace, workspace_id)
    if workspace is not None and not workspace.is_billable:
        return None  # Addendum §2.4: suppress all rate computation workspace-wide

    # 1. Task-level (highest priority)
    if task_id is not None:
        task = await db.get(Task, task_id)
        if task is not None and task.hourly_rate_cents is not None:
            return task.hourly_rate_cents

    # 2. Project-level
    project = await db.get(Project, project_id)
    if project is not None:
        if project.hourly_rate_cents is not None:
            return project.hourly_rate_cents

        # 3. Client-level (through project.client_id)
        if project.client_id is not None:
            client = await db.get(Client, project.client_id)
            if client is not None and client.hourly_rate_cents is not None:
                return client.hourly_rate_cents

    # 4. Workspace default (lowest priority)
    if workspace is not None and workspace.default_hourly_rate_cents is not None:
        return workspace.default_hourly_rate_cents

    return None
