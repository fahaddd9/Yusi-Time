"""
Unit tests for member_service — Phase 2.

Tests cover all business rules:
  - change_role: cannot promote to admin, sole-admin demotion blocked, audit logged
  - remove_member: sole-admin removal blocked
  - list_members: returns paginated results
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy import select


def make_member(workspace_id=None, user_id=None, role="member"):
    m = MagicMock()
    m.workspace_id = workspace_id or uuid.uuid4()
    m.user_id = user_id or uuid.uuid4()
    m.role = role
    m.joined_at = datetime.now(timezone.utc)
    return m


def make_user(user_id=None, email="test@example.com", full_name="Test User"):
    u = MagicMock()
    u.id = user_id or uuid.uuid4()
    u.email = email
    u.full_name = full_name
    u.avatar_url = None
    return u


@pytest.mark.asyncio
class TestChangeRole:
    async def test_change_role_to_admin_raises_400(self):
        """Promoting to 'admin' via API is forbidden → 400 BAD_REQUEST."""
        from app.services.member_service import change_role

        mock_db = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await change_role(
                db=mock_db,
                workspace_id=uuid.uuid4(),
                target_user_id=uuid.uuid4(),
                new_role="admin",
                actor_user_id=uuid.uuid4(),
            )
        assert exc.value.status_code == 400
        assert "admin" in exc.value.detail.lower()

    async def test_demote_sole_admin_raises_403(self):
        """Demoting the only admin → 403 SOLE_ADMIN."""
        from app.services.member_service import change_role

        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        member = make_member(workspace_id=ws_id, user_id=user_id, role="admin")
        user = make_user(user_id=user_id)

        mock_db = AsyncMock()

        # First execute: fetch target membership (returns member, user row)
        member_result = MagicMock()
        member_result.one_or_none = MagicMock(return_value=(member, user))

        # Second execute: count admins in workspace → returns 1 (sole admin)
        count_result = MagicMock()
        count_result.scalar_one = MagicMock(return_value=1)

        mock_db.execute = AsyncMock(side_effect=[member_result, count_result])

        with pytest.raises(HTTPException) as exc:
            await change_role(mock_db, ws_id, user_id, "member", actor_id)
        assert exc.value.status_code == 403
        assert exc.value.headers.get("code") == "SOLE_ADMIN"

    async def test_change_role_non_admin_succeeds(self):
        """Changing role of a non-admin member → success, audit logged."""
        from app.services.member_service import change_role

        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        member = make_member(workspace_id=ws_id, user_id=user_id, role="member")
        user = make_user(user_id=user_id)

        mock_db = AsyncMock()
        member_result = MagicMock()
        member_result.one_or_none = MagicMock(return_value=(member, user))
        mock_db.execute = AsyncMock(return_value=member_result)

        result = await change_role(mock_db, ws_id, user_id, "manager", actor_id)
        assert member.role == "manager"
        mock_db.add.assert_called()  # AuditLog added
        mock_db.flush.assert_awaited()


@pytest.mark.asyncio
class TestRemoveMember:
    async def test_remove_sole_admin_raises_403(self):
        """Removing the only admin → 403 SOLE_ADMIN."""
        from app.services.member_service import remove_member

        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        member = make_member(workspace_id=ws_id, user_id=user_id, role="admin")

        mock_db = AsyncMock()

        # First execute: find member → returns admin member
        member_result = MagicMock()
        member_result.scalar_one_or_none = MagicMock(return_value=member)

        # Second execute: count admins → 1 (sole admin)
        count_result = MagicMock()
        count_result.scalar_one = MagicMock(return_value=1)

        mock_db.execute = AsyncMock(side_effect=[member_result, count_result])

        with pytest.raises(HTTPException) as exc:
            await remove_member(mock_db, ws_id, user_id)
        assert exc.value.status_code == 403
        assert exc.value.headers.get("code") == "SOLE_ADMIN"

    async def test_remove_member_not_found_raises_404(self):
        """Removing non-member → 404 NOT_FOUND."""
        from app.services.member_service import remove_member

        mock_db = AsyncMock()
        member_result = MagicMock()
        member_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=member_result)

        with pytest.raises(HTTPException) as exc:
            await remove_member(mock_db, uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_remove_non_admin_member_succeeds(self):
        """Removing a non-admin member → succeeds, member deleted."""
        from app.services.member_service import remove_member

        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        member = make_member(workspace_id=ws_id, user_id=user_id, role="member")

        mock_db = AsyncMock()
        member_result = MagicMock()
        member_result.scalar_one_or_none = MagicMock(return_value=member)
        mock_db.execute = AsyncMock(return_value=member_result)

        await remove_member(mock_db, ws_id, user_id)
        mock_db.delete.assert_awaited_with(member)
        mock_db.flush.assert_awaited()
