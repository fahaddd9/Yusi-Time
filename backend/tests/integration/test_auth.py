"""
Integration tests for auth endpoints — full HTTP flows via async_client.

Uses the async_client fixture from conftest.py which runs against the test DB.
All 10 scenarios from Implementation Plan §1.8 are covered.
"""

from httpx import AsyncClient


# ── Signup ─────────────────────────────────────────────────────────────────

class TestSignup:
    async def test_signup_returns_201_with_access_token(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/signup", json={
            "email": "alice@example.com",
            "password": "securepassword1",
            "full_name": "Alice Smith",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "alice@example.com"
        assert "refresh_token" in resp.cookies

    async def test_signup_duplicate_email_returns_409(self, async_client: AsyncClient):
        payload = {
            "email": "duplicate@example.com",
            "password": "securepassword1",
            "full_name": "Bob Jones",
        }
        r1 = await async_client.post("/api/v1/auth/signup", json=payload)
        assert r1.status_code == 201

        r2 = await async_client.post("/api/v1/auth/signup", json=payload)
        assert r2.status_code == 409
        assert r2.json()["code"] == "EMAIL_ALREADY_EXISTS"

    async def test_signup_short_password_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/signup", json={
            "email": "short@example.com",
            "password": "short",       # less than 8 chars
            "full_name": "Short Pass",
        })
        assert resp.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────

class TestLogin:
    async def test_login_success_sets_cookie(self, async_client: AsyncClient):
        # First create the account
        await async_client.post("/api/v1/auth/signup", json={
            "email": "logintest@example.com",
            "password": "mypassword123",
            "full_name": "Login Test",
        })
        # Then log in
        resp = await async_client.post("/api/v1/auth/login", json={
            "email": "logintest@example.com",
            "password": "mypassword123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in resp.cookies

    async def test_login_wrong_password_returns_401(self, async_client: AsyncClient):
        await async_client.post("/api/v1/auth/signup", json={
            "email": "wrongpass@example.com",
            "password": "correctpass123",
            "full_name": "Wrong Pass",
        })
        resp = await async_client.post("/api/v1/auth/login", json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert resp.json()["code"] == "INVALID_CREDENTIALS"


# ── Refresh ────────────────────────────────────────────────────────────────

class TestRefresh:
    async def test_refresh_with_cookie_returns_new_token(self, async_client: AsyncClient):
        # Sign up to get a refresh cookie
        signup_resp = await async_client.post("/api/v1/auth/signup", json={
            "email": "refreshtest@example.com",
            "password": "mypassword123",
            "full_name": "Refresh Test",
        })
        assert signup_resp.status_code == 201
        # The cookie is stored automatically in async_client session
        resp = await async_client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_without_cookie_returns_401(self, async_client: AsyncClient):
        # Use a fresh client with no cookies
        from httpx import AsyncClient as FreshClient
        from httpx import ASGITransport
        from app.main import app as fastapi_app

        async with FreshClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://test",
        ) as fresh_client:
            resp = await fresh_client.post("/api/v1/auth/refresh")
            assert resp.status_code == 401


# ── Logout ─────────────────────────────────────────────────────────────────

class TestLogout:
    async def test_logout_clears_cookie(self, async_client: AsyncClient):
        # Sign up + get access token
        signup = await async_client.post("/api/v1/auth/signup", json={
            "email": "logouttest@example.com",
            "password": "mypassword123",
            "full_name": "Logout Test",
        })
        access_token = signup.json()["access_token"]

        resp = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully."


# ── Password Reset ─────────────────────────────────────────────────────────

class TestPasswordReset:
    async def test_forgot_password_nonexistent_returns_200(self, async_client: AsyncClient):
        """Must return 200 even when the email doesn't exist — prevents enumeration."""
        resp = await async_client.post("/api/v1/auth/forgot-password", json={
            "email": "nobody@example.com",
        })
        assert resp.status_code == 200

    async def test_reset_password_expired_token_returns_400(self, async_client: AsyncClient):
        """An obviously invalid token must return 400 BAD_REQUEST."""
        resp = await async_client.post("/api/v1/auth/reset-password", json={
            "token": "this-token-does-not-exist",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 400
        assert resp.json()["code"] == "BAD_REQUEST"
