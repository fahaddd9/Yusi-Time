import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.notification_service import (
    create,
    create_for_all_members,
    create_for_role,
    list_notifications,
    mark_read,
    mark_all_read
)
from app.models.notification import Notification
from app.models.workspace_member import WorkspaceMember

def make_db(members=None, count=0, notifications=None):
    db = AsyncMock()
    db.add = MagicMock()
    db.add_all = MagicMock()

    class MockResult:
        def __init__(self, items):
            self.items = items
        def scalars(self):
            class MockScalars:
                def __init__(self, items):
                    self.items = items
                def all(self):
                    return self.items
            return MockScalars(self.items)
        def scalar_one(self):
            return count

    async def _execute(stmt):
        if "count" in str(stmt).lower():
            return MockResult([])
        return MockResult(members or notifications or [])

    db.execute = AsyncMock(side_effect=_execute)
    return db

@pytest.mark.asyncio
async def test_create_notification():
    db = make_db()
    n = await create(
        db=db,
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        event_type="test_event",
        title="Test",
        message="Test message"
    )
    assert n.event_type == "test_event"
    assert db.add.called

@pytest.mark.asyncio
async def test_create_for_all_members():
    m1 = MagicMock(spec=WorkspaceMember)
    m1.user_id = uuid.uuid4()
    db = make_db(members=[m1])
    
    res = await create_for_all_members(
        db=db,
        workspace_id=uuid.uuid4(),
        event_type="test",
        title="Test",
        message="Message"
    )
    assert len(res) == 1
    assert res[0].user_id == m1.user_id
    assert db.add.called

@pytest.mark.asyncio
async def test_create_for_role():
    m1 = MagicMock(spec=WorkspaceMember)
    m1.user_id = uuid.uuid4()
    db = make_db(members=[m1.user_id]) # execute returns user_ids for this query
    
    await create_for_role(
        db=db,
        workspace_id=uuid.uuid4(),
        roles=["admin"],
        event_type="test",
        title="Test",
        message="Message"
    )
    assert db.add_all.called

@pytest.mark.asyncio
async def test_mark_read():
    db = make_db()
    db.execute = AsyncMock() # Just to accept the update stmt
    await mark_read(db, uuid.uuid4(), [uuid.uuid4()])
    assert db.execute.called

@pytest.mark.asyncio
async def test_mark_all_read():
    db = make_db()
    db.execute = AsyncMock()
    await mark_all_read(db, uuid.uuid4(), uuid.uuid4())
    assert db.execute.called
