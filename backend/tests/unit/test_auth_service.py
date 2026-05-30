"""
Unit tests for app/services/auth_service.py

Uses AsyncMock to mock the database session — no real DB required.
All 7 scenarios from the Implementation Plan §1.8 are covered.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import (
    register,
    login,
    initiate_password_reset,
    reset_password,
)
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken


def _make_user(
    *,
    is_active: bool = True,
    password_hash: str = "$argon2id$v=19$m=65536,t=3,p=4$fake",
    email: str = "test@example.com",
) -> User:
    u = User()
    u.id = uuid.uuid4()
    u.email = email
    u.password_hash = password_hash
    u.full_name = "Test User"
    u.is_active = is_active
    return u


def _make_db() -> AsyncMock:
    """Return a mock AsyncSession with the minimal API surface used by auth_service."""
    db = AsyncMock(spec=AsyncSession)
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _make_execute_result(obj):
    """Wrap a single ORM object in the structure returned by db.execute()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    result.scalars.return_value.all.return_value = []
    return result


# ── register() ────────────────────────────────────────────────────────────

class TestRegister:
    async def test_register_creates_user_workspace_member(self):
        db = _make_db()
        # No existing user
        db.execute.return_value = _make_execute_result(None)
        db.flush = AsyncMock()

        result = await register(db, "new@example.com", "password123", "Alice")

        assert result["access_token"]
        assert result["refresh_token"]
        assert result["user"].email == "new@example.com"
        assert result["workspace"].name == "Alice's Workspace"
        # add() should have been called 3 times: User, Workspace, WorkspaceMember
        assert db.add.call_count == 3

    async def test_register_duplicate_email_raises_409(self):
        db = _make_db()
        existing_user = _make_user(email="existing@example.com")
        db.execute.return_value = _make_execute_result(existing_user)

        with pytest.raises(HTTPException) as exc_info:
            await register(db, "existing@example.com", "password123", "Bob")

        assert exc_info.value.status_code == 409
        assert exc_info.value.headers["code"] == "EMAIL_ALREADY_EXISTS"


# ── login() ───────────────────────────────────────────────────────────────

class TestLogin:
    async def test_login_wrong_password_raises_401(self):
        db = _make_db()
        # Return a user whose hash will NOT match
        user = _make_user(password_hash="$argon2id$v=19$m=65536,t=3,p=4$fake_hash_will_not_match")
        db.execute.return_value = _make_execute_result(user)

        with pytest.raises(HTTPException) as exc_info:
            await login(db, "test@example.com", "wrong-password")

        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "INVALID_CREDENTIALS"

    async def test_login_inactive_user_raises_401(self):
        db = _make_db()
        user = _make_user(is_active=False)

        # verify_password will be patched to return True so we get past the password check
        with patch("app.services.auth_service.verify_password", return_value=True):
            db.execute.return_value = _make_execute_result(user)
            with pytest.raises(HTTPException) as exc_info:
                await login(db, "test@example.com", "any-password")

        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "INVALID_CREDENTIALS"

    async def test_login_unknown_email_raises_401(self):
        db = _make_db()
        db.execute.return_value = _make_execute_result(None)

        with pytest.raises(HTTPException) as exc_info:
            await login(db, "nobody@example.com", "any-password")

        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "INVALID_CREDENTIALS"


# ── reset_password() ──────────────────────────────────────────────────────

class TestResetPassword:
    def _make_token(self, *, used: bool = False, expired: bool = False) -> PasswordResetToken:
        t = PasswordResetToken()
        t.id = uuid.uuid4()
        t.user_id = uuid.uuid4()
        t.token = "valid-token-value"
        t.used = used
        now = datetime.now(timezone.utc)
        t.expires_at = now - timedelta(hours=2) if expired else now + timedelta(hours=1)
        return t

    async def test_reset_used_token_raises_400(self):
        db = _make_db()
        used_token = self._make_token(used=True)
        db.execute.return_value = _make_execute_result(used_token)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(db, "used-token", "newpassword123")

        assert exc_info.value.status_code == 400
        assert exc_info.value.headers["code"] == "BAD_REQUEST"

    async def test_reset_expired_token_raises_400(self):
        db = _make_db()
        expired_token = self._make_token(expired=True)
        db.execute.return_value = _make_execute_result(expired_token)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(db, "expired-token", "newpassword123")

        assert exc_info.value.status_code == 400
        assert exc_info.value.headers["code"] == "BAD_REQUEST"

    async def test_reset_missing_token_raises_400(self):
        db = _make_db()
        db.execute.return_value = _make_execute_result(None)

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(db, "nonexistent", "newpassword123")

        assert exc_info.value.status_code == 400


# ── initiate_password_reset() ─────────────────────────────────────────────

class TestInitiateReset:
    async def test_nonexistent_email_returns_silently(self):
        """Critical: must NOT raise any exception — prevents email enumeration."""
        db = _make_db()
        db.execute.return_value = _make_execute_result(None)

        # Should complete without raising
        result = await initiate_password_reset(db, "nobody@example.com")
        assert result is None  # function returns None silently
