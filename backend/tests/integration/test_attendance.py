"""
Integration tests for Phase 6.5 attendance and billable endpoints.
Addendum §4.1, §4.2, §4.4.

Tests use the real test DB via the async_client fixture (conftest.py).

Coverage:
  - PATCH /workspaces/{id}/attendance-settings (Admin only, 403 for Member)
  - PATCH /workspaces/{id}/billable-settings (Admin only)
  - GET /time-entries/daily-progress (Member only, 403 for Admin)
  - POST /time-entries/work-start-response "not_now"
  - GET /notifications/attendance — self scope and managed scope auth
  - Push subscription registration + unregistration
"""

from httpx import AsyncClient
import pytest
import uuid


@pytest.mark.asyncio
class TestAttendanceIntegration:

    # ── Setup helper ────────────────────────────────────────────────────────────

    async def setup_workspace(self, async_client: AsyncClient):
        """Create an Admin + Member pair with a shared workspace and project."""
        admin_email = f"admin_{uuid.uuid4()}@example.com"
        member_email = f"member_{uuid.uuid4()}@example.com"

        # Admin signup → creates workspace
        r = await async_client.post("/api/v1/auth/signup", json={
            "email": admin_email,
            "password": "password123",
            "full_name": "Admin User",
        })
        assert r.status_code == 201, r.text
        admin_token = r.json()["access_token"]
        ws_id = r.json()["workspace"]["id"]

        # Create a project for timer tests
        r = await async_client.post(
            "/api/v1/projects",
            params={"workspace_id": ws_id},
            json={"name": "Attendance Test Project", "visibility": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201, r.text
        project_id = r.json()["data"]["id"]

        # Invite + signup member
        invite = await async_client.post(
            f"/api/v1/workspaces/{ws_id}/invites",
            json={"email": member_email, "role": "member"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        token = invite.json()["token"]

        r = await async_client.post("/api/v1/auth/signup", json={
            "email": member_email,
            "password": "password123",
            "full_name": "Member User",
        })
        member_token = r.json()["access_token"]

        await async_client.post(
            f"/api/v1/invites/{token}/accept",
            headers={"Authorization": f"Bearer {member_token}"},
        )

        return admin_token, member_token, ws_id, project_id

    # ── PATCH /attendance-settings ──────────────────────────────────────────────

    async def test_admin_can_update_attendance_settings(self, async_client: AsyncClient):
        """Admin successfully patches attendance settings."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/attendance-settings",
            json={
                "attendance_enabled": True,
                "attendance_mode": "fixed_schedule",
                "work_start_time": "09:00",
                "daily_required_hours": 8.0,
                "off_days": [0, 6],  # Sunday and Saturday off
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["attendance_enabled"] is True
        assert data["attendance_mode"] == "fixed_schedule"
        assert data["daily_required_hours"] == 8.0
        assert 0 in data["off_days"]
        assert 6 in data["off_days"]

    async def test_member_cannot_update_attendance_settings(self, async_client: AsyncClient):
        """Member is forbidden from patching attendance settings (Admin only)."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/attendance-settings",
            json={"attendance_enabled": True},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 403, r.text

    async def test_invalid_off_days_value_rejected(self, async_client: AsyncClient):
        """off_days value 7 (out of range) is rejected with 422."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/attendance-settings",
            json={"off_days": [7]},  # 7 is invalid (0-6 only)
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422, r.text

    async def test_invalid_work_start_time_rejected(self, async_client: AsyncClient):
        """work_start_time in wrong format is rejected with 422."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/attendance-settings",
            json={"work_start_time": "9am"},  # must be HH:MM
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422, r.text

    # ── PATCH /billable-settings ────────────────────────────────────────────────

    async def test_admin_can_disable_billable(self, async_client: AsyncClient):
        """Admin successfully disables billable tracking."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/billable-settings",
            json={"is_billable": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["is_billable"] is False

    async def test_admin_can_re_enable_billable(self, async_client: AsyncClient):
        """Admin can toggle is_billable back to True (PRD-ADD-06)."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        # Disable
        await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/billable-settings",
            json={"is_billable": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Re-enable
        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/billable-settings",
            json={"is_billable": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["is_billable"] is True

    async def test_member_cannot_update_billable_settings(self, async_client: AsyncClient):
        """Member is forbidden from patching billable settings."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/billable-settings",
            json={"is_billable": False},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 403, r.text

    # ── GET /time-entries/daily-progress ──────────────────────────────────────

    async def test_member_can_get_daily_progress(self, async_client: AsyncClient):
        """Member successfully gets daily-progress — on_pace=True when no target set."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.get(
            "/api/v1/time-entries/daily-progress",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "hours_logged_today" in data
        assert "on_pace" in data
        # No target configured → daily_required_hours is None
        assert data["daily_required_hours"] is None
        assert data["on_pace"] is True

    async def test_admin_cannot_get_daily_progress(self, async_client: AsyncClient):
        """Admin role is excluded from daily-progress (PRD-ADD-03)."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.get(
            "/api/v1/time-entries/daily-progress",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Admin cannot access Member-only endpoint
        assert r.status_code == 403, r.text

    async def test_daily_progress_shows_hours_when_target_set(self, async_client: AsyncClient):
        """After setting daily_required_hours, response includes it."""
        admin_token, member_token, ws_id, _ = await self.setup_workspace(async_client)

        # Admin enables attendance with 8h target
        await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/attendance-settings",
            json={"attendance_enabled": True, "daily_required_hours": 8.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        r = await async_client.get(
            "/api/v1/time-entries/daily-progress",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["daily_required_hours"] == 8.0

    # ── POST /time-entries/work-start-response ────────────────────────────────

    async def test_member_not_now_response(self, async_client: AsyncClient):
        """Member 'not_now' creates notification and returns acknowledged."""
        admin_token, member_token, ws_id, _ = await self.setup_workspace(async_client)

        # Enable attendance first
        await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/attendance-settings",
            json={
                "attendance_enabled": True,
                "attendance_mode": "fixed_schedule",
                "work_start_time": "09:00",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        r = await async_client.post(
            "/api/v1/time-entries/work-start-response",
            params={"workspace_id": ws_id},
            json={"response": "not_now"},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["acknowledged"] is True
        assert data["time_entry_id"] is None

    async def test_start_response_requires_project_id(self, async_client: AsyncClient):
        """'start' response without project_id returns 422 (schema validation)."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.post(
            "/api/v1/time-entries/work-start-response",
            params={"workspace_id": ws_id},
            json={"response": "start"},  # missing project_id
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 422, r.text

    async def test_admin_cannot_post_work_start_response(self, async_client: AsyncClient):
        """Admin role is excluded from work-start-response (PRD-ADD-03)."""
        admin_token, _, ws_id, project_id = await self.setup_workspace(async_client)

        r = await async_client.post(
            "/api/v1/time-entries/work-start-response",
            params={"workspace_id": ws_id},
            json={"response": "not_now"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 403, r.text

    # ── GET /notifications/attendance ─────────────────────────────────────────

    async def test_member_can_get_self_scope_notifications(self, async_client: AsyncClient):
        """Member can retrieve their own attendance notifications (scope=self)."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.get(
            "/api/v1/notifications/attendance",
            params={"workspace_id": ws_id, "scope": "self"},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "data" in data
        assert "total" in data
        assert "unread_count" in data
        assert "page" in data
        assert "per_page" in data

    async def test_member_cannot_get_managed_scope(self, async_client: AsyncClient):
        """Member requesting managed scope is forbidden (403)."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.get(
            "/api/v1/notifications/attendance",
            params={"workspace_id": ws_id, "scope": "managed"},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 403, r.text

    async def test_admin_can_get_managed_scope(self, async_client: AsyncClient):
        """Admin can request managed scope to see all workspace attendance notifs."""
        admin_token, _, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.get(
            "/api/v1/notifications/attendance",
            params={"workspace_id": ws_id, "scope": "managed"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text

    async def test_pagination_params_respected(self, async_client: AsyncClient):
        """per_page and page are reflected in the response."""
        _, member_token, ws_id, _ = await self.setup_workspace(async_client)

        r = await async_client.get(
            "/api/v1/notifications/attendance",
            params={"workspace_id": ws_id, "scope": "self", "page": 2, "per_page": 5},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["page"] == 2
        assert data["per_page"] == 5

    # ── Push Subscription ─────────────────────────────────────────────────────

    async def test_register_push_subscription(self, async_client: AsyncClient):
        """Successfully register a push subscription for a user."""
        admin_token, _, _, _ = await self.setup_workspace(async_client)

        r = await async_client.post(
            "/api/v1/users/me/push-subscriptions",
            json={
                "endpoint": "https://fcm.googleapis.com/fcm/send/fake-endpoint",
                "p256dh_key": "BNcRdreALRFXTkOOUHK1EtK2wtBZuE8kYp-AAAAAAAA",
                "auth_key": "tBHItJI5svbpez7KI4CCXg",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["endpoint"] == "https://fcm.googleapis.com/fcm/send/fake-endpoint"
        assert "id" in data
        sub_id = data["id"]

        # Delete the subscription
        r = await async_client.delete(
            f"/api/v1/users/me/push-subscriptions/{sub_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 204, r.text

    async def test_upsert_push_subscription_same_endpoint(self, async_client: AsyncClient):
        """Registering the same endpoint twice updates the keys (upsert, not 409)."""
        admin_token, _, _, _ = await self.setup_workspace(async_client)
        endpoint = "https://fcm.googleapis.com/fcm/send/same-endpoint"

        # First registration
        r1 = await async_client.post(
            "/api/v1/users/me/push-subscriptions",
            json={
                "endpoint": endpoint,
                "p256dh_key": "AAAAAAAAAAA",
                "auth_key": "BBBBBBB",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r1.status_code == 201, r1.text

        # Second registration with same endpoint — should 201 again (upsert)
        r2 = await async_client.post(
            "/api/v1/users/me/push-subscriptions",
            json={
                "endpoint": endpoint,
                "p256dh_key": "CCCCCCCCCCC",
                "auth_key": "DDDDDDD",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r2.status_code == 201, r2.text

    async def test_delete_other_users_subscription_is_404(self, async_client: AsyncClient):
        """A user cannot delete another user's push subscription (returns 404)."""
        admin_token, member_token, _, _ = await self.setup_workspace(async_client)

        # Admin registers a subscription
        r = await async_client.post(
            "/api/v1/users/me/push-subscriptions",
            json={
                "endpoint": "https://fcm.googleapis.com/fcm/send/admin-sub",
                "p256dh_key": "AAAAAAAA",
                "auth_key": "BBBBBBBB",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        sub_id = r.json()["id"]

        # Member tries to delete admin's subscription
        r = await async_client.delete(
            f"/api/v1/users/me/push-subscriptions/{sub_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 404, r.text
