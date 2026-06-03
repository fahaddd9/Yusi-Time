import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.project_service import (
    list_projects,
    get_project,
    create_project,
    update_project,
    archive_project,
    delete_project,
    list_project_members,
    add_project_member,
    remove_project_member
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate

def make_project(**kwargs) -> Project:
    return Project(
        id=kwargs.get("id", uuid.uuid4()),
        workspace_id=kwargs.get("workspace_id", uuid.uuid4()),
        name=kwargs.get("name", "Test Project"),
        client_id=kwargs.get("client_id", None),
        visibility=kwargs.get("visibility", "public"),
        status=kwargs.get("status", "active")
    )

@pytest.mark.asyncio
async def test_list_projects():
    mock_db = AsyncMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1
    
    mock_fetch_result = MagicMock()
    p = make_project()
    mock_fetch_result.all.return_value = [(p, "Test Client", 10.5)]
    
    mock_db.execute.side_effect = [mock_count_result, mock_fetch_result]
    
    projects, total = await list_projects(
        mock_db, uuid.uuid4(), uuid.uuid4(), "admin", "active", None, 1, 20
    )
    assert total == 1
    assert len(projects) == 1
    assert projects[0]["name"] == "Test Project"
    assert projects[0]["client_name"] == "Test Client"
    assert projects[0]["hours_logged"] == 10.5

@pytest.mark.asyncio
async def test_list_projects_empty():
    mock_db = AsyncMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 0
    mock_db.execute.side_effect = [mock_count_result]
    
    projects, total = await list_projects(
        mock_db, uuid.uuid4(), uuid.uuid4(), "admin", "active", None, 1, 20
    )
    assert total == 0
    assert len(projects) == 0

@pytest.mark.asyncio
async def test_create_project_success():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_dup

    data = ProjectCreate(name="New Proj")
    project = await create_project(mock_db, uuid.uuid4(), data)
    assert project.name == "New Proj"
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()

@pytest.mark.asyncio
async def test_create_project_duplicate():
    mock_db = AsyncMock()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = make_project()
    mock_db.execute.return_value = mock_dup

    data = ProjectCreate(name="Dup Proj")
    with pytest.raises(HTTPException) as exc:
        await create_project(mock_db, uuid.uuid4(), data)
    assert exc.value.status_code == 409

@pytest.mark.asyncio
async def test_create_project_client_not_found():
    mock_db = AsyncMock()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None
    
    mock_client = MagicMock()
    mock_client.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_dup, mock_client]

    data = ProjectCreate(name="New Proj", client_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        await create_project(mock_db, uuid.uuid4(), data)
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_get_project_success():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    p = make_project()
    mock_res.first.return_value = (p, "Client Name")
    mock_db.execute.return_value = mock_res
    
    res = await get_project(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "admin")
    assert res["name"] == "Test Project"
    assert res["client_name"] == "Client Name"

@pytest.mark.asyncio
async def test_get_project_not_found():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.first.return_value = None
    mock_db.execute.return_value = mock_res
    
    with pytest.raises(HTTPException) as exc:
        await get_project(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "admin")
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_update_project_success():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    p = make_project(name="Old Name")
    mock_res.scalar_one_or_none.return_value = p
    
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_res, mock_dup]
    
    data = ProjectUpdate(name="New Name")
    res = await update_project(mock_db, uuid.uuid4(), uuid.uuid4(), data)
    assert res.name == "New Name"
    mock_db.flush.assert_called_once()

@pytest.mark.asyncio
async def test_update_project_not_found():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res
    
    data = ProjectUpdate(name="New Name")
    with pytest.raises(HTTPException) as exc:
        await update_project(mock_db, uuid.uuid4(), uuid.uuid4(), data)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_archive_project_success():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    p = make_project()
    mock_res.scalar_one_or_none.return_value = p
    mock_db.execute.return_value = mock_res
    
    res = await archive_project(mock_db, uuid.uuid4(), uuid.uuid4())
    assert res.status == "archived"
    assert res.archived_at is not None

@pytest.mark.asyncio
async def test_delete_project_success():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    p = make_project()
    mock_res.scalar_one_or_none.return_value = p
    
    mock_count = MagicMock()
    mock_count.scalar.return_value = 0
    
    mock_db.execute.side_effect = [mock_res, mock_count]
    
    await delete_project(mock_db, uuid.uuid4(), uuid.uuid4())
    mock_db.delete.assert_called_once_with(p)

@pytest.mark.asyncio
async def test_delete_project_has_time_entries():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    p = make_project()
    mock_res.scalar_one_or_none.return_value = p
    
    mock_count = MagicMock()
    mock_count.scalar.return_value = 5
    
    mock_db.execute.side_effect = [mock_res, mock_count]
    
    with pytest.raises(HTTPException) as exc:
        await delete_project(mock_db, uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_list_project_members():
    mock_db = AsyncMock()
    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = make_project()
    mock_res2 = MagicMock()
    mock_res2.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
    mock_db.execute.side_effect = [mock_res1, mock_res2]
    
    res = await list_project_members(mock_db, uuid.uuid4(), uuid.uuid4())
    assert len(res) == 2

@pytest.mark.asyncio
async def test_add_project_member():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = make_project()
    mock_res2 = MagicMock()
    mock_res2.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_res1, mock_res2]
    
    res = await add_project_member(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    assert res is not None
    mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_add_project_member_duplicate():
    mock_db = AsyncMock()
    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = make_project()
    mock_res2 = MagicMock()
    mock_res2.scalar_one_or_none.return_value = MagicMock()
    mock_db.execute.side_effect = [mock_res1, mock_res2]
    
    with pytest.raises(HTTPException) as exc:
        await add_project_member(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 409

@pytest.mark.asyncio
async def test_remove_project_member():
    mock_db = AsyncMock()
    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = make_project()
    mock_res2 = MagicMock()
    pm = MagicMock(spec=ProjectMember)
    mock_res2.scalar_one_or_none.return_value = pm
    mock_db.execute.side_effect = [mock_res1, mock_res2]
    
    await remove_project_member(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    mock_db.delete.assert_called_once_with(pm)

@pytest.mark.asyncio
async def test_list_projects_filters():
    mock_db = AsyncMock()
    mock_count = MagicMock()
    mock_count.scalar.return_value = 1
    mock_fetch = MagicMock()
    mock_fetch.all.return_value = [(make_project(), "Client", 10.0)]
    mock_db.execute.side_effect = [mock_count, mock_fetch]
    
    projects, total = await list_projects(mock_db, uuid.uuid4(), uuid.uuid4(), "member", "all", uuid.uuid4(), 1, 20)
    assert total == 1

@pytest.mark.asyncio
async def test_get_project_member_role():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.first.return_value = (make_project(), "Client Name")
    mock_db.execute.return_value = mock_res
    res = await get_project(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "member")
    assert res["name"] == "Test Project"

@pytest.mark.asyncio
async def test_update_project_duplicate():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = make_project(name="Old Name")
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = make_project(name="Dup Name")
    mock_db.execute.side_effect = [mock_res, mock_dup]
    with pytest.raises(HTTPException) as exc:
        await update_project(mock_db, uuid.uuid4(), uuid.uuid4(), ProjectUpdate(name="Dup Name"))
    assert exc.value.status_code == 409

@pytest.mark.asyncio
async def test_project_not_found_branches():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res
    
    with pytest.raises(HTTPException):
        await archive_project(mock_db, uuid.uuid4(), uuid.uuid4())
    with pytest.raises(HTTPException):
        await delete_project(mock_db, uuid.uuid4(), uuid.uuid4())
    with pytest.raises(HTTPException):
        await list_project_members(mock_db, uuid.uuid4(), uuid.uuid4())
    with pytest.raises(HTTPException):
        await add_project_member(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    with pytest.raises(HTTPException):
        await remove_project_member(mock_db, uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
