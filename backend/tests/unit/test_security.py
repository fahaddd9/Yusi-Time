"""
Unit tests for app/core/security.py

Tests are synchronous — no DB, no HTTP, no async needed.
All 5 scenarios from the Implementation Plan §1.2 are covered:
  1. hash_password + verify_password round-trip
  2. Wrong password returns False (no exception raised)
  3. create_access_token + verify_access_token round-trip
  4. Expired token raises HTTP 401 TOKEN_EXPIRED
  5. Wrong secret raises HTTP 401 UNAUTHENTICATED

Plus coverage for refresh tokens and the type-guard protection.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    generate_secure_token,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_settings():
    s = MagicMock()
    s.jwt_secret = "test-access-secret-do-not-use-in-production"
    s.jwt_refresh_secret = "test-refresh-secret-do-not-use-in-production"
    s.access_token_expire_minutes = 30
    s.refresh_token_expire_days = 7
    return s


USER_ID = "550e8400-e29b-41d4-a716-446655440000"


# ── Password tests ─────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MyPassword123!")
        assert hashed != "MyPassword123!"

    def test_verify_correct_password_returns_true(self):
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_wrong_password_returns_false_no_exception(self):
        """
        Critical: must return False, never raise — callers raise 401 themselves.
        """
        hashed = hash_password("correct-password")
        result = verify_password("wrong-password", hashed)
        assert result is False

    def test_two_hashes_of_same_password_are_different(self):
        """Argon2 uses random salts — hashes must never be identical."""
        p = "same-password"
        assert hash_password(p) != hash_password(p)

    def test_verify_with_garbage_hash_returns_false(self):
        """Handles corrupted/invalid hash gracefully."""
        assert verify_password("anything", "not-a-valid-argon2-hash") is False


# ── Access token tests ─────────────────────────────────────────────────────

class TestAccessToken:
    def test_create_and_verify_round_trip(self, mock_settings):
        token = create_access_token(USER_ID, mock_settings)
        payload = verify_access_token(token, mock_settings.jwt_secret)
        assert payload["sub"] == USER_ID
        assert payload["type"] == "access"

    def test_expired_token_raises_401_token_expired(self, mock_settings):
        """Manually craft an already-expired token."""
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": USER_ID,
            "type": "access",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),  # already expired
        }
        expired_token = jwt.encode(
            expired_payload, mock_settings.jwt_secret, algorithm="HS256"
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(expired_token, mock_settings.jwt_secret)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "TOKEN_EXPIRED"

    def test_wrong_secret_raises_401_unauthenticated(self, mock_settings):
        token = create_access_token(USER_ID, mock_settings)
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(token, "completely-wrong-secret")
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "UNAUTHENTICATED"

    def test_refresh_token_rejected_as_access_token(self, mock_settings):
        """Type-guard: a refresh token cannot be used where an access token is expected."""
        refresh_token = create_refresh_token(USER_ID, mock_settings)
        with pytest.raises(HTTPException) as exc_info:
            # Verify the refresh token using the access-token secret
            # Even if it decoded, type != "access" should reject it
            verify_access_token(refresh_token, mock_settings.jwt_refresh_secret)
        assert exc_info.value.status_code == 401

    def test_malformed_token_raises_401(self, mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token("this.is.not.a.jwt", mock_settings.jwt_secret)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "UNAUTHENTICATED"


# ── Refresh token tests ────────────────────────────────────────────────────

class TestRefreshToken:
    def test_create_and_verify_round_trip(self, mock_settings):
        token = create_refresh_token(USER_ID, mock_settings)
        payload = verify_refresh_token(token, mock_settings.jwt_refresh_secret)
        assert payload["sub"] == USER_ID
        assert payload["type"] == "refresh"

    def test_expired_refresh_token_raises_401(self, mock_settings):
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": USER_ID,
            "type": "refresh",
            "iat": now - timedelta(days=8),
            "exp": now - timedelta(days=1),
        }
        expired_token = jwt.encode(
            expired_payload, mock_settings.jwt_refresh_secret, algorithm="HS256"
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_refresh_token(expired_token, mock_settings.jwt_refresh_secret)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["code"] == "TOKEN_EXPIRED"

    def test_access_token_rejected_as_refresh_token(self, mock_settings):
        """Type-guard: an access token cannot be used where a refresh token is expected."""
        access_token = create_access_token(USER_ID, mock_settings)
        with pytest.raises(HTTPException) as exc_info:
            verify_refresh_token(access_token, mock_settings.jwt_secret)
        assert exc_info.value.status_code == 401


# ── Secure token tests ─────────────────────────────────────────────────────

class TestGenerateSecureToken:
    def test_returns_string(self):
        token = generate_secure_token()
        assert isinstance(token, str)

    def test_minimum_length(self):
        """32 bytes base64-encoded = at least 43 chars."""
        token = generate_secure_token()
        assert len(token) >= 43

    def test_tokens_are_unique(self):
        tokens = {generate_secure_token() for _ in range(100)}
        assert len(tokens) == 100  # all unique

    def test_url_safe(self):
        """Must not contain +, /, or = (URL-safe base64)."""
        token = generate_secure_token()
        assert "+" not in token
        assert "/" not in token
        assert "=" not in token
