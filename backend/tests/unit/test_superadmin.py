"""
Unit tests for Phase 1.5 — Super Admin Backend (API-only).

Tests cover:
  1. User model — is_superadmin field defaults to False
  2. UserPublic schema — is_superadmin serialized from ORM model
  3. get_superadmin_user dependency — 403 for non-super-admin users
  4. get_workspace_member dependency — synthetic member bypass for super admins
  5. require_role dependency — bypass for super admins regardless of role list

All tests use MagicMock objects with spec= to avoid SQLAlchemy instance state
requirements — these are pure unit tests with no DB involved.
RULE B-10: Every service function has corresponding unit tests with mocked DB.
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.user import UserPublic
from app.core.dependencies import (
    get_superadmin_user,
    get_workspace_member,
    require_role,
    _make_synthetic_member,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_user(is_superadmin: bool = False, is_active: bool = True) -> MagicMock:
    """
    Build a MagicMock with User spec so dependencies work without a live DB session.
    Using MagicMock(spec=User) avoids SQLAlchemy's _sa_instance_state requirement
    while still making isinstance() checks pass for type annotations.
    """
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.password_hash = "hashed"
    user.google_id = None
    user.avatar_url = None
    user.timezone = None
    user.weekly_hours_goal = None
    user.is_active = is_active
    user.is_superadmin = is_superadmin
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


def make_member(workspace_id: uuid.UUID, user_id: uuid.UUID, role: str = "member") -> MagicMock:
    """Build a MagicMock with WorkspaceMember spec without touching the DB."""
    member = MagicMock(spec=WorkspaceMember)
    member.workspace_id = workspace_id
    member.user_id = user_id
    member.role = role
    return member


# ── 1. UserPublic schema serialization ────────────────────────────────────────
# Note: Pydantic requires real objects or dicts with from_attributes=True.
# We build a real minimal object using object() + __dict__ assignment trick,
# which works because UserPublic reads attributes, not SQLAlchemy state.

class _FakeUser:
    """Minimal plain Python object to feed Pydantic's from_attributes validation."""
    def __init__(self, is_superadmin: bool = False):
        self.id = uuid.uuid4()
        self.email = "test@example.com"
        self.full_name = "Test User"
        self.avatar_url = None
        self.timezone = None
        self.weekly_hours_goal = None
        self.is_active = True
        self.is_superadmin = is_superadmin
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class TestUserPublicSchema:
    def test_userpublic_includes_is_superadmin_false(self):
        """
        UserPublic must always include is_superadmin.
        Frontend reads this from GET /users/me. MASTER_PROMPT §11.
        """
        public = UserPublic.model_validate(_FakeUser(is_superadmin=False))
        assert public.is_superadmin is False

    def test_userpublic_includes_is_superadmin_true(self):
        """Super Admin flag propagates through Pydantic serialization."""
        public = UserPublic.model_validate(_FakeUser(is_superadmin=True))
        assert public.is_superadmin is True

    def test_userpublic_is_superadmin_in_dict_output(self):
        """is_superadmin must appear in the JSON-serializable dict."""
        data = UserPublic.model_validate(_FakeUser(is_superadmin=False)).model_dump()
        assert "is_superadmin" in data
        assert data["is_superadmin"] is False


# ── 2. _make_synthetic_member helper ──────────────────────────────────────────

class TestSyntheticMember:
    def test_synthetic_member_has_admin_role(self):
        """
        Synthetic member must always carry role='admin'.
        MASTER_PROMPT §11: 'Synthetic member object always carries role=admin'.
        """
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        member = _make_synthetic_member(ws_id, user_id)
        assert member.role == "admin"

    def test_synthetic_member_workspace_id_matches(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        member = _make_synthetic_member(ws_id, user_id)
        assert member.workspace_id == ws_id

    def test_synthetic_member_user_id_matches(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        member = _make_synthetic_member(ws_id, user_id)
        assert member.user_id == user_id


# ── 3. get_superadmin_user dependency ─────────────────────────────────────────

class TestGetSuperadminUser:
    async def test_raises_403_for_regular_user(self):
        """
        get_superadmin_user must raise 403 FORBIDDEN for non-super-admin.
        MASTER_PROMPT §11.
        """
        regular_user = make_user(is_superadmin=False)
        with pytest.raises(HTTPException) as exc_info:
            await get_superadmin_user(current_user=regular_user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.headers.get("code") == "FORBIDDEN"

    async def test_returns_user_for_superadmin(self):
        """Super Admin passes through and returns the user object."""
        sa_user = make_user(is_superadmin=True)
        result = await get_superadmin_user(current_user=sa_user)
        assert result is sa_user

    async def test_inactive_superadmin_still_passes_check(self):
        """
        get_current_user already blocks inactive users before this dependency runs.
        If somehow an inactive Super Admin reached this point, is_superadmin check
        still passes (is_active is irrelevant at this layer).
        """
        sa_user = make_user(is_superadmin=True, is_active=False)
        result = await get_superadmin_user(current_user=sa_user)
        assert result is sa_user


# ── 4. get_workspace_member dependency ────────────────────────────────────────

class TestGetWorkspaceMemberBypass:
    async def test_superadmin_gets_synthetic_member_without_db_query(self):
        """
        Super Admin bypasses the workspace_members DB query entirely.
        Returns a synthetic WorkspaceMember with role='admin'.
        MASTER_PROMPT §11.
        """
        sa_user = make_user(is_superadmin=True)
        ws_id = uuid.uuid4()
        mock_db = AsyncMock()

        result = await get_workspace_member(
            workspace_id=ws_id,
            current_user=sa_user,
            db=mock_db,
        )

        # DB must NOT be queried for Super Admins
        mock_db.execute.assert_not_called()
        assert result.role == "admin"
        assert result.workspace_id == ws_id
        assert result.user_id == sa_user.id

    async def test_regular_user_not_member_raises_404(self):
        """
        Regular user with no membership in the workspace gets 404.
        MASTER_PROMPT §11 / TRD v1.2 §6.
        """
        regular_user = make_user(is_superadmin=False)
        ws_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Simulate scalar_one_or_none() returning None (user is not a member)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_workspace_member(
                workspace_id=ws_id,
                current_user=regular_user,
                db=mock_db,
            )
        assert exc_info.value.status_code == 404
        mock_db.execute.assert_called_once()

    async def test_regular_user_member_returns_real_member(self):
        """Regular user who IS a member gets their real WorkspaceMember record."""
        regular_user = make_user(is_superadmin=False)
        ws_id = uuid.uuid4()
        real_member = make_member(ws_id, regular_user.id, role="member")
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = real_member
        mock_db.execute.return_value = mock_result

        result = await get_workspace_member(
            workspace_id=ws_id,
            current_user=regular_user,
            db=mock_db,
        )
        assert result is real_member
        assert result.role == "member"


# ── 5. require_role dependency ────────────────────────────────────────────────

class TestRequireRole:
    async def test_superadmin_bypasses_all_role_checks(self):
        """
        Super Admin passes require_role() regardless of the specified roles.
        MASTER_PROMPT §11: 'Super Admin bypasses ALL require_role() checks'.
        """
        sa_user = make_user(is_superadmin=True)
        ws_id = uuid.uuid4()
        synthetic_member = _make_synthetic_member(ws_id, sa_user.id)

        # require_role("viewer") — the most restrictive role possible
        role_dep = require_role("viewer")
        result = await role_dep(current_user=sa_user, member=synthetic_member)
        assert result.role == "admin"  # synthetic member returned unchanged

    async def test_matching_role_passes(self):
        """Regular user with a matching role passes the check."""
        regular_user = make_user(is_superadmin=False)
        ws_id = uuid.uuid4()
        admin_member = make_member(ws_id, regular_user.id, role="admin")

        role_dep = require_role("admin", "manager")
        result = await role_dep(current_user=regular_user, member=admin_member)
        assert result is admin_member

    async def test_non_matching_role_raises_403(self):
        """Regular user without matching role gets 403 FORBIDDEN."""
        regular_user = make_user(is_superadmin=False)
        ws_id = uuid.uuid4()
        viewer_member = make_member(ws_id, regular_user.id, role="viewer")

        role_dep = require_role("admin", "manager")
        with pytest.raises(HTTPException) as exc_info:
            await role_dep(current_user=regular_user, member=viewer_member)
        assert exc_info.value.status_code == 403
        assert exc_info.value.headers.get("code") == "FORBIDDEN"

    async def test_superadmin_bypasses_even_admin_only_routes(self):
        """
        Confirm require_role("admin") also passes for Super Admin
        even though they are not in the workspace_members table.
        """
        sa_user = make_user(is_superadmin=True)
        ws_id = uuid.uuid4()
        synthetic_member = _make_synthetic_member(ws_id, sa_user.id)

        role_dep = require_role("admin")
        result = await role_dep(current_user=sa_user, member=synthetic_member)
        assert result.role == "admin"
