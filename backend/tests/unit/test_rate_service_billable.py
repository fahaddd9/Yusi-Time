"""
Unit tests for rate_service.py — Phase 6.5 is_billable short-circuit.
Addendum §2.4, PRD-ADD-05, PRD-ADD-06.

Tests verify:
  1. is_billable=False short-circuits entire rate hierarchy → None
  2. Existing rate data is NOT mutated (PRD-ADD-06)
  3. Full hierarchy still works when is_billable=True
  4. Short-circuit wins over any configured rate (task, project, client, workspace)
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.task import Task
from app.models.client import Client
from app.services.rate_service import resolve_rate


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_workspace(is_billable=True, default_hourly_rate_cents=None):
    ws = MagicMock(spec=Workspace)
    ws.id = uuid.uuid4()
    ws.is_billable = is_billable
    ws.default_hourly_rate_cents = default_hourly_rate_cents
    return ws


def make_project(hourly_rate_cents=None, client_id=None):
    p = MagicMock(spec=Project)
    p.id = uuid.uuid4()
    p.hourly_rate_cents = hourly_rate_cents
    p.client_id = client_id
    return p


def make_task(hourly_rate_cents=None):
    t = MagicMock(spec=Task)
    t.id = uuid.uuid4()
    t.hourly_rate_cents = hourly_rate_cents
    return t


def make_client(hourly_rate_cents=None):
    c = MagicMock(spec=Client)
    c.id = uuid.uuid4()
    c.hourly_rate_cents = hourly_rate_cents
    return c


def make_db(workspace=None, project=None, task=None, client=None):
    db = AsyncMock()

    async def _get(cls, pk):
        if cls is Workspace:
            return workspace
        if cls is Project:
            return project
        if cls is Task:
            return task
        if cls is Client:
            return client
        return None

    db.get = AsyncMock(side_effect=_get)
    return db


# ── PRD-ADD-05: is_billable=False short-circuit ────────────────────────────────

@pytest.mark.asyncio
class TestIsBillableShortCircuit:

    async def test_returns_none_when_workspace_not_billable(self):
        """PRD-ADD-05: is_billable=False → resolve_rate returns None immediately."""
        ws = make_workspace(is_billable=False, default_hourly_rate_cents=5000)
        project = make_project(hourly_rate_cents=8000)
        task = make_task(hourly_rate_cents=10000)
        db = make_db(workspace=ws, project=project, task=task)

        result = await resolve_rate(
            db=db,
            workspace_id=ws.id,
            project_id=project.id,
            task_id=task.id,
        )

        # Short-circuit must win regardless of configured rates at any level
        assert result is None

    async def test_short_circuit_wins_over_task_rate(self):
        """PRD-ADD-05: is_billable=False wins even when task has a rate."""
        ws = make_workspace(is_billable=False)
        project = make_project()
        task = make_task(hourly_rate_cents=15000)
        db = make_db(workspace=ws, project=project, task=task)

        result = await resolve_rate(db, ws.id, project.id, task.id)

        assert result is None

    async def test_short_circuit_wins_over_client_rate(self):
        """PRD-ADD-05: is_billable=False wins even when client has a rate."""
        client = make_client(hourly_rate_cents=6000)
        ws = make_workspace(is_billable=False)
        project = make_project(client_id=client.id)
        db = make_db(workspace=ws, project=project, client=client)

        result = await resolve_rate(db, ws.id, project.id, None)

        assert result is None

    async def test_stored_rates_not_modified(self):
        """PRD-ADD-06: Existing rate data is never touched when is_billable=False."""
        ws = make_workspace(is_billable=False, default_hourly_rate_cents=5000)
        project = make_project(hourly_rate_cents=8000)
        task = make_task(hourly_rate_cents=10000)
        db = make_db(workspace=ws, project=project, task=task)

        await resolve_rate(db, ws.id, project.id, task.id)

        # Verify none of the stored rate data was mutated
        assert ws.default_hourly_rate_cents == 5000   # unchanged
        assert project.hourly_rate_cents == 8000        # unchanged
        assert task.hourly_rate_cents == 10000          # unchanged

    async def test_billable_true_falls_through_to_task(self):
        """With is_billable=True, hierarchy applies normally: task takes precedence."""
        ws = make_workspace(is_billable=True, default_hourly_rate_cents=3000)
        project = make_project(hourly_rate_cents=6000)
        task = make_task(hourly_rate_cents=12000)
        db = make_db(workspace=ws, project=project, task=task)

        result = await resolve_rate(db, ws.id, project.id, task.id)

        assert result == 12000  # task wins

    async def test_billable_true_falls_through_to_project(self):
        """With is_billable=True, no task rate → project rate applies."""
        ws = make_workspace(is_billable=True, default_hourly_rate_cents=3000)
        project = make_project(hourly_rate_cents=6000)
        task = make_task(hourly_rate_cents=None)
        db = make_db(workspace=ws, project=project, task=task)

        result = await resolve_rate(db, ws.id, project.id, task.id)

        assert result == 6000  # project wins

    async def test_billable_true_falls_through_to_client(self):
        """With is_billable=True, no task/project rate → client rate applies."""
        client = make_client(hourly_rate_cents=7500)
        ws = make_workspace(is_billable=True, default_hourly_rate_cents=3000)
        project = make_project(hourly_rate_cents=None, client_id=client.id)
        db = make_db(workspace=ws, project=project, client=client)

        result = await resolve_rate(db, ws.id, project.id, None)

        assert result == 7500  # client wins

    async def test_billable_true_falls_through_to_workspace(self):
        """With is_billable=True, no task/project/client rate → workspace default."""
        ws = make_workspace(is_billable=True, default_hourly_rate_cents=4000)
        project = make_project(hourly_rate_cents=None)
        db = make_db(workspace=ws, project=project)

        result = await resolve_rate(db, ws.id, project.id, None)

        assert result == 4000  # workspace default

    async def test_returns_none_when_no_rate_configured(self):
        """With is_billable=True and no rates anywhere, returns None."""
        ws = make_workspace(is_billable=True, default_hourly_rate_cents=None)
        project = make_project(hourly_rate_cents=None)
        db = make_db(workspace=ws, project=project)

        result = await resolve_rate(db, ws.id, project.id, None)

        assert result is None

    async def test_toggle_restores_rate(self):
        """PRD-ADD-06: After toggling back to is_billable=True, rates are resolved normally."""
        ws = make_workspace(is_billable=True, default_hourly_rate_cents=5000)
        project = make_project(hourly_rate_cents=None)
        db = make_db(workspace=ws, project=project)

        # Previously is_billable=False would have returned None.
        # Now is_billable=True — should resolve to workspace rate again.
        result = await resolve_rate(db, ws.id, project.id, None)

        assert result == 5000
