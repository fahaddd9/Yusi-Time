"""
Rate Service — Unit Tests
Implementation Plan §4.3 — all 4 levels + fallthrough logic.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock


def make_task(rate_cents=None):
    t = MagicMock()
    t.hourly_rate_cents = rate_cents
    return t


def make_project(rate_cents=None, client_id=None):
    p = MagicMock()
    p.hourly_rate_cents = rate_cents
    p.client_id = client_id
    return p


def make_client(rate_cents=None):
    c = MagicMock()
    c.hourly_rate_cents = rate_cents
    return c


def make_workspace(rate_cents=None):
    w = MagicMock()
    w.default_hourly_rate_cents = rate_cents
    return w


def make_db(task=None, project=None, client=None, workspace=None):
    """Build a mock AsyncSession whose .get() returns appropriate objects."""
    from app.models.task import Task
    from app.models.project import Project
    from app.models.client import Client
    from app.models.workspace import Workspace

    db = AsyncMock()

    async def _get(model_class, pk):
        if model_class is Task:
            return task
        if model_class is Project:
            return project
        if model_class is Client:
            return client
        if model_class is Workspace:
            return workspace
        return None

    db.get = _get
    return db


# ─── Level 1: Task rate (highest priority) ────────────────────────────────────

@pytest.mark.asyncio
async def test_task_rate_wins_when_set():
    db = make_db(
        task=make_task(rate_cents=5000),
        project=make_project(rate_cents=4000),
        client=make_client(rate_cents=3000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    ws_id, proj_id, task_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    result = await resolve_rate(db, ws_id, proj_id, task_id)
    assert result == 5000


@pytest.mark.asyncio
async def test_task_none_rate_falls_through_to_project():
    db = make_db(
        task=make_task(rate_cents=None),   # task has no rate
        project=make_project(rate_cents=4000),
        client=make_client(rate_cents=3000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    assert result == 4000


# ─── Level 2: Project rate ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_project_rate_wins_when_no_task_rate():
    db = make_db(
        task=None,   # no task
        project=make_project(rate_cents=4000),
        client=make_client(rate_cents=3000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 4000


@pytest.mark.asyncio
async def test_project_none_rate_falls_through_to_client():
    client_id = uuid.uuid4()
    db = make_db(
        task=None,
        project=make_project(rate_cents=None, client_id=client_id),
        client=make_client(rate_cents=3000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 3000


# ─── Level 3: Client rate ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_client_rate_wins_when_no_task_or_project_rate():
    client_id = uuid.uuid4()
    db = make_db(
        task=None,
        project=make_project(rate_cents=None, client_id=client_id),
        client=make_client(rate_cents=3000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 3000


@pytest.mark.asyncio
async def test_no_client_falls_through_to_workspace():
    # project has no client_id
    db = make_db(
        task=None,
        project=make_project(rate_cents=None, client_id=None),  # no client
        client=make_client(rate_cents=3000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 2000


# ─── Level 4: Workspace default (lowest priority) ─────────────────────────────

@pytest.mark.asyncio
async def test_workspace_default_used_when_nothing_else_set():
    db = make_db(
        task=None,
        project=make_project(rate_cents=None, client_id=None),
        client=None,
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 2000


@pytest.mark.asyncio
async def test_returns_none_when_no_rate_at_any_level():
    db = make_db(
        task=None,
        project=make_project(rate_cents=None, client_id=None),
        client=None,
        workspace=make_workspace(rate_cents=None),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result is None


# ─── Edge cases ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_task_id_none_skips_task_lookup():
    """When task_id is None, task level is skipped — project rate should be used."""
    db = make_db(
        task=make_task(rate_cents=9999),  # would win if task_id were provided
        project=make_project(rate_cents=4000),
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 4000


@pytest.mark.asyncio
async def test_project_not_found_falls_through_to_workspace():
    """If project doesn't exist (returns None), skip to workspace."""
    db = make_db(
        task=None,
        project=None,  # project not found
        workspace=make_workspace(rate_cents=2000),
    )
    from app.services.rate_service import resolve_rate
    result = await resolve_rate(db, uuid.uuid4(), uuid.uuid4(), task_id=None)
    assert result == 2000
