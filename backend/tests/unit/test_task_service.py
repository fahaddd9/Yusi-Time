import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.task_service import (
    list_tasks,
    get_task,
    create_task,
    update_task,
    delete_task
)
from app.models.task import Task
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate
from tests.unit.test_project_service import make_project

def make_task(**kwargs) -> Task:
    return Task(
        id=kwargs.get("id", uuid.uuid4()),
        workspace_id=kwargs.get("workspace_id", uuid.uuid4()),
        project_id=kwargs.get("project_id", uuid.uuid4()),
        name=kwargs.get("name", "Test Task")
    )

@pytest.mark.asyncio
async def test_list_tasks_success():
    mock_db = AsyncMock()
    
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = MagicMock(spec=Project)
    
    mock_count = MagicMock()
    mock_count.scalar.return_value = 2
    
    mock_fetch = MagicMock()
    mock_fetch.scalars.return_value.all.return_value = [make_task(), make_task()]
    
    mock_db.execute.side_effect = [mock_proj, mock_count, mock_fetch]
    
    tasks, total = await list_tasks(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "admin", 1, 20)
    assert total == 2
    assert len(tasks) == 2

@pytest.mark.asyncio
async def test_list_tasks_empty():
    mock_db = AsyncMock()
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = MagicMock(spec=Project)
    
    mock_count = MagicMock()
    mock_count.scalar.return_value = 0
    
    mock_db.execute.side_effect = [mock_proj, mock_count]
    
    tasks, total = await list_tasks(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "member", 1, 20)
    assert total == 0
    assert len(tasks) == 0

@pytest.mark.asyncio
async def test_list_tasks_project_not_found():
    mock_db = AsyncMock()
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_proj
    
    with pytest.raises(HTTPException) as exc:
        await list_tasks(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "member", 1, 20)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_get_task_success():
    mock_db = AsyncMock()
    
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = MagicMock(spec=Project)
    
    mock_task = MagicMock()
    t = make_task()
    mock_task.scalar_one_or_none.return_value = t
    
    mock_db.execute.side_effect = [mock_proj, mock_task]
    
    res = await get_task(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "admin")
    assert res == t

@pytest.mark.asyncio
async def test_get_task_not_found():
    mock_db = AsyncMock()
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = MagicMock(spec=Project)
    
    mock_task = MagicMock()
    mock_task.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_proj, mock_task]
    
    with pytest.raises(HTTPException) as exc:
        await get_task(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "admin")
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_create_task_success():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = MagicMock(spec=Project)
    
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_proj, mock_dup]
    
    data = TaskCreate(project_id=uuid.uuid4(), name="New Task")
    t = await create_task(mock_db, uuid.uuid4(), data)
    assert t.name == "New Task"
    mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_create_task_assignee_not_found():
    mock_db = AsyncMock()
    
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = MagicMock(spec=Project)
    
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None
    
    mock_member = MagicMock()
    mock_member.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_proj, mock_dup, mock_member]
    
    data = TaskCreate(project_id=uuid.uuid4(), name="New Task", assignee_user_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        await create_task(mock_db, uuid.uuid4(), data)
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_update_task_success():
    mock_db = AsyncMock()
    
    mock_task = MagicMock()
    t = make_task(name="Old Name")
    mock_task.scalar_one_or_none.return_value = t
    
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_task, mock_dup]
    
    data = TaskUpdate(name="New Name")
    res = await update_task(mock_db, uuid.uuid4(), uuid.uuid4(), data)
    assert res.name == "New Name"
    mock_db.flush.assert_called_once()

@pytest.mark.asyncio
async def test_delete_task_success():
    mock_db = AsyncMock()
    
    mock_task = MagicMock()
    t = make_task()
    mock_task.scalar_one_or_none.return_value = t
    
    mock_db.execute.return_value = mock_task
    
    await delete_task(mock_db, uuid.uuid4(), uuid.uuid4())
    mock_db.delete.assert_called_once_with(t)

@pytest.mark.asyncio
async def test_get_task_member_role():
    mock_db = AsyncMock()
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = make_project()
    mock_task = MagicMock()
    mock_task.scalar_one_or_none.return_value = make_task()
    mock_db.execute.side_effect = [mock_proj, mock_task]
    res = await get_task(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "member")
    assert res is not None

@pytest.mark.asyncio
async def test_task_not_found_branches():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res
    with pytest.raises(HTTPException):
        await update_task(mock_db, uuid.uuid4(), uuid.uuid4(), TaskUpdate(name="New"))
    with pytest.raises(HTTPException):
        await delete_task(mock_db, uuid.uuid4(), uuid.uuid4())

@pytest.mark.asyncio
async def test_create_task_duplicate():
    mock_db = AsyncMock()
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = make_project()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = make_task()
    mock_db.execute.side_effect = [mock_proj, mock_dup]
    with pytest.raises(HTTPException) as exc:
        await create_task(mock_db, uuid.uuid4(), TaskCreate(project_id=uuid.uuid4(), name="Dup"))
    assert exc.value.status_code == 409

@pytest.mark.asyncio
async def test_update_task_duplicate_and_assignee():
    mock_db = AsyncMock()
    mock_task = MagicMock()
    mock_task.scalar_one_or_none.return_value = make_task(name="Old")
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = make_task(name="Dup")
    mock_db.execute.side_effect = [mock_task, mock_dup]
    with pytest.raises(HTTPException) as exc:
        await update_task(mock_db, uuid.uuid4(), uuid.uuid4(), TaskUpdate(name="Dup"))
    assert exc.value.status_code == 409

    mock_db.execute.side_effect = [mock_task, MagicMock(scalar_one_or_none=lambda: None), MagicMock(scalar_one_or_none=lambda: None)]
    with pytest.raises(HTTPException) as exc:
        await update_task(mock_db, uuid.uuid4(), uuid.uuid4(), TaskUpdate(name="New", assignee_user_id=uuid.uuid4()))
    assert exc.value.status_code == 400
