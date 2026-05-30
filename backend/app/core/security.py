"""
Security utilities — password hashing, JWT creation/verification, token generation.

Design decisions:
  - Argon2id for password hashing (argon2-cffi). Modern, memory-hard, resistant
    to GPU attacks. Superior to bcrypt in every dimension.
  - python-jose for JWT. Encodes/decodes HS256 signed tokens.
  - Access tokens carry: sub (user_id), type="access", iat, exp
  - Refresh tokens carry: sub (user_id), type="refresh", iat, exp
  - Token type is verified on decode to prevent refresh tokens being used as
    access tokens (and vice versa).
  - HTTPException codes are string headers ("code": "TOKEN_EXPIRED") so the
    frontend API client can branch on the exact error without parsing message text.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import secrets
from fastapi import HTTPException

_ph = PasswordHasher()


# ── Password hashing ───────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return an Argon2 hash of the plaintext password."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify plaintext against an Argon2 hash.
    Returns False on mismatch — never raises. Callers decide what to do.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ── JWT tokens ─────────────────────────────────────────────────────────────


def create_access_token(user_id: str, settings) -> str:
    """
    Create a short-lived HS256 JWT access token.
    Expiry: settings.access_token_expire_minutes (default 30 min).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: str, settings) -> str:
    """
    Create a long-lived HS256 JWT refresh token.
    Expiry: settings.refresh_token_expire_days (default 7 days).
    Stored in an HttpOnly cookie — never in JS-accessible storage.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm="HS256")


def verify_access_token(token: str, jwt_secret: str) -> dict:
    """
    Decode and validate an access token.
    Raises HTTP 401 with a machine-readable "code" header on any failure.
    """
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type",
                headers={"code": "UNAUTHENTICATED"},
            )
        return payload
    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"code": "TOKEN_EXPIRED"},
            )
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"code": "UNAUTHENTICATED"},
        )


def verify_refresh_token(token: str, jwt_refresh_secret: str) -> dict:
    """
    Decode and validate a refresh token.
    Used exclusively by POST /auth/refresh.
    """
    try:
        payload = jwt.decode(token, jwt_refresh_secret, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type",
                headers={"code": "UNAUTHENTICATED"},
            )
        return payload
    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise HTTPException(
                status_code=401,
                detail="Refresh token expired",
                headers={"code": "TOKEN_EXPIRED"},
            )
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"code": "UNAUTHENTICATED"},
        )


# ── Secure random tokens ───────────────────────────────────────────────────


def generate_secure_token() -> str:
    """
    Generate a URL-safe base64 random token for password reset links
    and invite links. 32 bytes = 256 bits of entropy.
    """
    return secrets.token_urlsafe(32)
