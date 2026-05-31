"""
Integration tests for Phase 1.5 — Super Admin Backend (API-only).

Uses async_client fixture from conftest.py (real test DB, full HTTP stack).

Tests verify:
  1. New users created via /auth/signup always have is_superadmin=false in response
  2. is_superadmin field is present in UserPublic output from /auth/signup
  3. Super Admin bypass: a user promoted to is_superadmin=True in the DB can
     access a workspace they are not a member of (via synthetic member injection)
  4. get_superadmin_user dependency correctly rejects non-super-admin users

Phase 1.5 has NO endpoints of its own — the bypass is infrastructure. So
integration tests validate the infrastructure through the auth endpoints and
by directly manipulating is_superadmin in the test DB.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.core.dependencies import get_workspace_member, get_superadmin_user


# ── Helper ─────────────────────────────────────────────────────────────────────

async def promote_to_superadmin(db: AsyncSession, email: str) -> None:
    """Directly set is_superadmin=True for a user by email (mimics operator DB access)."""
    await db.execute(
        update(User)
        .where(User.email == email.lower())
        .values(is_superadmin=True)
    )
    await db.commit()


# ── 1. Signup response includes is_superadmin=false ───────────────────────────

class TestSignupIncludesSuperadminField:
    async def test_new_user_has_is_superadmin_false(self, async_client: AsyncClient):
        """
        POST /auth/signup must return is_superadmin=False for every new user
        in the embedded user object of the response body.

        MASTER_PROMPT §11: 'Always FALSE on newly created users regardless of signup method'.
        The UserEmbedded schema in SignupResponse must always include is_superadmin.
        """
        resp = await async_client.post("/api/v1/auth/signup", json={
            "email": "sa_check@example.com",
            "password": "securepassword1",
            "full_name": "SA Check User",
        })
        assert resp.status_code == 201
        body = resp.json()
        # UserEmbedded is nested under "user" in the SignupResponse
        assert "user" in body
        user_data = body["user"]
        assert "is_superadmin" in user_data, (
            f"is_superadmin must always be present in UserEmbedded. "
            f"Got keys: {list(user_data.keys())}"
        )
        assert user_data["is_superadmin"] is False


# ── 2. Super Admin DB promotion and bypass ─────────────────────────────────────

class TestSuperAdminBypass:
    async def test_promoted_user_is_superadmin_in_db(self, async_client: AsyncClient):
        """
        After direct DB promotion, the user's is_superadmin flag must read True.
        This simulates what the seed_superadmin.py operator script does.
        """
        # First create a user
        resp = await async_client.post("/api/v1/auth/signup", json={
            "email": "promote_test@example.com",
            "password": "securepassword1",
            "full_name": "Promote Test",
        })
        assert resp.status_code == 201

        # Use the app's test DB dependency directly to promote them
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.core.config import get_settings
        settings = get_settings()
        engine = create_async_engine(settings.test_database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            await promote_to_superadmin(db, "promote_test@example.com")

            from sqlalchemy import select, func
            result = await db.execute(
                select(User).where(func.lower(User.email) == "promote_test@example.com")
            )
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.is_superadmin is True

        await engine.dispose()

    async def test_superadmin_get_workspace_member_returns_synthetic(self, async_client: AsyncClient):
        """
        A Super Admin calling get_workspace_member for a workspace they are NOT
        a member of must receive a synthetic WorkspaceMember(role='admin')
        instead of a 404.

        This validates the full bypass chain end-to-end using the dependency
        layer directly against the test DB.
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import select
        from app.core.config import get_settings
        settings = get_settings()

        engine = create_async_engine(settings.test_database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Create a Super Admin user
            from app.core.security import hash_password
            sa_user = User(
                email="sa_bypass_test@example.com",
                password_hash=hash_password("password123"),
                full_name="SA Bypass Test",
                is_active=True,
                is_superadmin=True,
            )
            db.add(sa_user)
            await db.flush()
            sa_user_id = sa_user.id
            await db.commit()

            # Create an unrelated workspace (SA is NOT a member of it)
            unrelated_ws = Workspace(name="Unrelated Workspace")
            db.add(unrelated_ws)
            await db.flush()
            unrelated_ws_id = unrelated_ws.id
            await db.commit()

            # Reload SA user fresh from DB
            result = await db.execute(select(User).where(User.id == sa_user_id))
            sa_user_fresh = result.scalar_one()
            assert sa_user_fresh.is_superadmin is True

            # Verify SA is NOT in workspace_members for this workspace
            member_result = await db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == unrelated_ws_id,
                    WorkspaceMember.user_id == sa_user_id,
                )
            )
            assert member_result.scalar_one_or_none() is None, \
                "SA should not be a real member of this workspace"

            # Now call get_workspace_member — should return synthetic admin member
            synthetic = await get_workspace_member(
                workspace_id=unrelated_ws_id,
                current_user=sa_user_fresh,
                db=db,
            )
            assert synthetic.role == "admin"
            assert synthetic.workspace_id == unrelated_ws_id
            assert synthetic.user_id == sa_user_id

        await engine.dispose()

    async def test_non_superadmin_cannot_access_foreign_workspace(self, async_client: AsyncClient):
        """
        A regular user who is NOT a member of a workspace gets 404, not bypass.
        Confirms the bypass is exclusive to Super Admins.
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import select
        from app.core.config import get_settings
        from fastapi import HTTPException
        settings = get_settings()

        engine = create_async_engine(settings.test_database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            from app.core.security import hash_password
            regular_user = User(
                email="regular_no_access@example.com",
                password_hash=hash_password("password123"),
                full_name="Regular User",
                is_active=True,
                is_superadmin=False,
            )
            db.add(regular_user)
            await db.flush()
            user_id = regular_user.id

            unrelated_ws = Workspace(name="Another Unrelated Workspace")
            db.add(unrelated_ws)
            await db.flush()
            ws_id = unrelated_ws.id
            await db.commit()

            result = await db.execute(select(User).where(User.id == user_id))
            user_fresh = result.scalar_one()
            assert user_fresh.is_superadmin is False

            # Should raise 404 for a regular user with no membership
            with pytest.raises(HTTPException) as exc_info:
                await get_workspace_member(
                    workspace_id=ws_id,
                    current_user=user_fresh,
                    db=db,
                )
            assert exc_info.value.status_code == 404

        await engine.dispose()


# ── 3. get_superadmin_user dependency end-to-end ──────────────────────────────

class TestGetSuperadminUserIntegration:
    async def test_regular_user_rejected_by_get_superadmin_user(self, async_client: AsyncClient):
        """
        A regular authenticated user hitting get_superadmin_user gets 403.
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import select
        from app.core.config import get_settings
        from fastapi import HTTPException
        settings = get_settings()

        engine = create_async_engine(settings.test_database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            from app.core.security import hash_password
            reg_user = User(
                email="reject_sa_dep@example.com",
                password_hash=hash_password("password123"),
                full_name="Reject SA Dep",
                is_active=True,
                is_superadmin=False,
            )
            db.add(reg_user)
            await db.flush()
            user_id = reg_user.id
            await db.commit()

            result = await db.execute(select(User).where(User.id == user_id))
            user_fresh = result.scalar_one()

            with pytest.raises(HTTPException) as exc_info:
                await get_superadmin_user(current_user=user_fresh)
            assert exc_info.value.status_code == 403
            assert exc_info.value.headers["code"] == "FORBIDDEN"

        await engine.dispose()

    async def test_superadmin_passes_get_superadmin_user(self, async_client: AsyncClient):
        """A user with is_superadmin=True passes get_superadmin_user."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import select
        from app.core.config import get_settings
        settings = get_settings()

        engine = create_async_engine(settings.test_database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            from app.core.security import hash_password
            sa_user = User(
                email="pass_sa_dep@example.com",
                password_hash=hash_password("password123"),
                full_name="Pass SA Dep",
                is_active=True,
                is_superadmin=True,
            )
            db.add(sa_user)
            await db.flush()
            user_id = sa_user.id
            await db.commit()

            result = await db.execute(select(User).where(User.id == user_id))
            user_fresh = result.scalar_one()

            returned = await get_superadmin_user(current_user=user_fresh)
            assert returned.id == user_id
            assert returned.is_superadmin is True

        await engine.dispose()
