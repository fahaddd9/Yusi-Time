"""
Rate service — Implementation Plan §4.3, TRD v1.2 §6.6.

Resolves the effective hourly rate for a time entry using the 4-level hierarchy:
  1. Task-level rate (highest priority)
  2. Project-level rate
  3. Client-level rate
  4. Workspace default rate (lowest priority)
  5. None if no rate is defined at any level

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

    Rate hierarchy (PRD §5 Rate Snapshot, Implementation Plan §4.3):
      1. Task.hourly_rate_cents  — if task_id is provided and task has a rate
      2. Project.hourly_rate_cents — if project has a rate
      3. Client.hourly_rate_cents — if project has a client and client has a rate
      4. Workspace.default_hourly_rate_cents — workspace default

    The result is snapshotted onto the time entry at creation/edit time.
    Subsequent rate changes do NOT affect already-saved entries.
    """
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
    workspace = await db.get(Workspace, workspace_id)
    if workspace is not None and workspace.default_hourly_rate_cents is not None:
        return workspace.default_hourly_rate_cents

    return None
