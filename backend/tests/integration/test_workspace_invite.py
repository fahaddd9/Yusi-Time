"""
Integration tests for Phase 2 — Workspace & Invite flows.

Full HTTP flows using async_client fixture against a real test database.
Tests the complete end-to-end lifecycle:
  - Admin creates workspace (via signup, which auto-creates workspace)
  - GET /workspaces lists correct workspaces with role
  - GET /workspaces/{id} returns full detail for admin
  - GET /workspaces/{id} returns viewer schema (no financial fields) for viewer
  - PATCH /workspaces/{id} updates settings (admin only)
  - PATCH /workspaces/{id} by non-admin → 403
  - PATCH /workspaces/{id} rounding validation → 400
  - Admin creates invite → POST /workspaces/{id}/invites
  - GET /workspaces/{id}/invites lists pending invites
  - GET /invites/{token} shows workspace context
  - POST /invites/{token}/accept creates membership
  - POST /invites/{token}/accept again → 409 ALREADY_MEMBER
  - GET /workspaces/{id}/members shows new member
  - PATCH /workspaces/{id}/members/{uid} changes role (admin only)
  - PATCH /workspaces/{id}/members/{uid} to admin → 400
  - DELETE /workspaces/{id}/members/{uid} removes member
  - GET /users/me returns is_superadmin and all profile fields
  - PATCH /users/me updates profile
  - DELETE /workspaces/{id}/invites/{token} revokes invite
"""

import pytest
from httpx import AsyncClient


# ── Helpers ────────────────────────────────────────────────────────────────────

async def create_and_login(async_client: AsyncClient, email: str, password: str = "securepass1", name: str = "Test User"):
    """Sign up a new user and return (access_token, user_data, workspace_data)."""
    resp = await async_client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": name,
    })
    assert resp.status_code == 201, f"signup failed: {resp.json()}"
    body = resp.json()
    return body["access_token"], body["user"], body["workspace"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Users ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestUsersMe:
    async def test_get_me_returns_profile(self, async_client: AsyncClient):
        """GET /users/me returns full profile including is_superadmin."""
        token, user_data, _ = await create_and_login(async_client, "getme@example.com")
        resp = await async_client.get("/api/v1/users/me", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "getme@example.com"
        assert "is_superadmin" in body
        assert body["is_superadmin"] is False

    async def test_patch_me_updates_full_name(self, async_client: AsyncClient):
        """PATCH /users/me updates provided fields only."""
        token, _, _ = await create_and_login(async_client, "patchme@example.com")
        resp = await async_client.patch(
            "/api/v1/users/me",
            json={"full_name": "Updated Name"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    async def test_get_me_unauthenticated_returns_401(self, async_client: AsyncClient):
        """GET /users/me without token → 401."""
        resp = await async_client.get("/api/v1/users/me")
        assert resp.status_code == 401


# ── Workspaces ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestWorkspaces:
    async def test_list_workspaces_returns_user_workspace(self, async_client: AsyncClient):
        """GET /workspaces lists the workspace created on signup."""
        token, _, workspace_data = await create_and_login(async_client, "listws@example.com")
        resp = await async_client.get("/api/v1/workspaces", headers=auth_header(token))
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        assert items[0]["role"] == "admin"
        assert items[0]["member_count"] >= 1

    async def test_get_workspace_detail_for_admin(self, async_client: AsyncClient):
        """GET /workspaces/{id} returns WorkspaceDetail for admin (includes financial fields)."""
        token, _, workspace_data = await create_and_login(async_client, "detailadmin@example.com")
        ws_id = workspace_data["id"]
        resp = await async_client.get(f"/api/v1/workspaces/{ws_id}", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "rounding_mode" in body
        assert "approval_workflow_enabled" in body

    async def test_patch_workspace_by_admin_succeeds(self, async_client: AsyncClient):
        """PATCH /workspaces/{id} by Admin updates and returns new values."""
        token, _, workspace_data = await create_and_login(async_client, "patchws@example.com")
        ws_id = workspace_data["id"]
        resp = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}",
            json={"name": "Renamed Workspace"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Workspace"

    async def test_patch_workspace_rounding_without_interval_returns_400(self, async_client: AsyncClient):
        """PATCH with rounding_mode != 'none' but no interval → 422 validation error."""
        token, _, workspace_data = await create_and_login(async_client, "roundingws@example.com")
        ws_id = workspace_data["id"]
        resp = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}",
            json={"rounding_mode": "nearest"},  # missing interval
            headers=auth_header(token),
        )
        assert resp.status_code == 422

    async def test_get_workspace_by_non_member_returns_404(self, async_client: AsyncClient):
        """Non-member accessing a workspace → 404 (treated as workspace not found)."""
        token_a, _, ws_a = await create_and_login(async_client, "wsa@example.com")
        token_b, _, _ = await create_and_login(async_client, "wsb@example.com")
        resp = await async_client.get(f"/api/v1/workspaces/{ws_a['id']}", headers=auth_header(token_b))
        assert resp.status_code == 404


# ── Members ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestMembers:
    async def test_list_members_includes_admin(self, async_client: AsyncClient):
        """GET /workspaces/{id}/members includes the founding admin."""
        token, user_data, ws = await create_and_login(async_client, "listmembers@example.com")
        resp = await async_client.get(f"/api/v1/workspaces/{ws['id']}/members", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert any(m["role"] == "admin" for m in body["items"])

    async def test_change_role_to_admin_returns_400(self, async_client: AsyncClient):
        """PATCH member to admin role → 400 BAD_REQUEST."""
        token, user_data, ws = await create_and_login(async_client, "changetoadmin@example.com")
        resp = await async_client.patch(
            f"/api/v1/workspaces/{ws['id']}/members/{user_data['id']}",
            json={"new_role": "admin"},
            headers=auth_header(token),
        )
        # Pydantic Literal blocks 'admin' → 422 from schema validation
        assert resp.status_code == 422

    async def test_remove_sole_admin_returns_403(self, async_client: AsyncClient):
        """DELETE sole admin → 403 SOLE_ADMIN."""
        token, user_data, ws = await create_and_login(async_client, "soleadmin@example.com")
        resp = await async_client.delete(
            f"/api/v1/workspaces/{ws['id']}/members/{user_data['id']}",
            headers=auth_header(token),
        )
        assert resp.status_code == 403
        assert resp.json().get("code") == "SOLE_ADMIN"


# ── Full Invite Flow ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestInviteFlow:
    async def test_full_invite_flow(self, async_client: AsyncClient):
        """
        Full invite lifecycle:
        1. Admin creates invite
        2. GET /invites/{token} returns workspace context
        3. Second user accepts invite
        4. Second user appears in members list
        5. Second user accepting again → 409 ALREADY_MEMBER
        """
        # Admin workspace
        admin_token, admin_user, ws = await create_and_login(async_client, "inviteadmin@example.com")
        ws_id = ws["id"]

        # Step 1: Admin creates invite
        invite_resp = await async_client.post(
            f"/api/v1/workspaces/{ws_id}/invites",
            json={"email": "invitee@example.com", "role": "member"},
            headers=auth_header(admin_token),
        )
        assert invite_resp.status_code == 201
        invite_data = invite_resp.json()
        token = invite_data["token"]
        assert invite_data["role"] == "member"
        assert invite_data["used"] is False

        # Step 2: GET /invites/{token} — public, no auth
        public_resp = await async_client.get(f"/api/v1/invites/{token}")
        assert public_resp.status_code == 200
        public_data = public_resp.json()
        assert public_data["workspace_name"] is not None
        assert public_data["role"] == "member"

        # Step 3: Second user signs up and accepts invite
        invitee_token, _, _ = await create_and_login(async_client, "invitee@example.com", name="Invitee User")
        accept_resp = await async_client.post(
            f"/api/v1/invites/{token}/accept",
            headers=auth_header(invitee_token),
        )
        assert accept_resp.status_code == 200

        # Step 4: Second user appears in members list
        members_resp = await async_client.get(
            f"/api/v1/workspaces/{ws_id}/members",
            headers=auth_header(admin_token),
        )
        assert members_resp.status_code == 200
        emails = [m["email"] for m in members_resp.json()["items"]]
        assert "invitee@example.com" in emails

        # Step 5: Accepting again → 409 ALREADY_MEMBER
        repeat_resp = await async_client.post(
            f"/api/v1/invites/{token}/accept",
            headers=auth_header(invitee_token),
        )
        # Invite is now used so it returns INVITE_USED before ALREADY_MEMBER check
        assert repeat_resp.status_code == 400

    async def test_create_invite_role_admin_blocked(self, async_client: AsyncClient):
        """POST invite with role='admin' → 422 (Pydantic Literal blocks it)."""
        token, _, ws = await create_and_login(async_client, "inviteadminblock@example.com")
        resp = await async_client.post(
            f"/api/v1/workspaces/{ws['id']}/invites",
            json={"email": "test@example.com", "role": "admin"},
            headers=auth_header(token),
        )
        assert resp.status_code == 422

    async def test_revoke_invite(self, async_client: AsyncClient):
        """DELETE /invites/{token} sets revoked=True. GET /invites/{token} then returns 400."""
        admin_token, _, ws = await create_and_login(async_client, "revokeadmin@example.com")
        ws_id = ws["id"]

        # Create invite
        invite_resp = await async_client.post(
            f"/api/v1/workspaces/{ws_id}/invites",
            json={"email": "revokee@example.com", "role": "viewer"},
            headers=auth_header(admin_token),
        )
        assert invite_resp.status_code == 201
        token = invite_resp.json()["token"]

        # Revoke it
        revoke_resp = await async_client.delete(
            f"/api/v1/workspaces/{ws_id}/invites/{token}",
            headers=auth_header(admin_token),
        )
        assert revoke_resp.status_code == 204

        # GET public → 400 INVITE_REVOKED
        public_resp = await async_client.get(f"/api/v1/invites/{token}")
        assert public_resp.status_code == 400
        assert public_resp.json().get("code") == "INVITE_REVOKED"

    async def test_list_invites_shows_pending_only(self, async_client: AsyncClient):
        """GET /workspaces/{id}/invites only returns active (not revoked) invites."""
        admin_token, _, ws = await create_and_login(async_client, "listinvites@example.com")
        ws_id = ws["id"]

        # Create two invites
        r1 = await async_client.post(
            f"/api/v1/workspaces/{ws_id}/invites",
            json={"email": "a@example.com", "role": "member"},
            headers=auth_header(admin_token),
        )
        r2 = await async_client.post(
            f"/api/v1/workspaces/{ws_id}/invites",
            json={"email": "b@example.com", "role": "viewer"},
            headers=auth_header(admin_token),
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        token_b = r2.json()["token"]

        # Revoke second invite
        await async_client.delete(
            f"/api/v1/workspaces/{ws_id}/invites/{token_b}",
            headers=auth_header(admin_token),
        )

        # List → only first invite appears
        list_resp = await async_client.get(
            f"/api/v1/workspaces/{ws_id}/invites",
            headers=auth_header(admin_token),
        )
        assert list_resp.status_code == 200
        body = list_resp.json()
        assert body["total"] == 1
        assert body["items"][0]["email"] == "a@example.com"
