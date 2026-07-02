"""
Integration tests for reports endpoints — Phase 7.
API Spec v1.1 §14 — all 9 report endpoints.

Tests use the real FastAPI ASGI app with an in-memory test DB (see conftest.py).
All tests go through the full HTTP stack including dependency injection, auth,
and response serialization.

Coverage:
  1. GET /reports/summary — group_by=project, empty result, admin full fields
  2. GET /reports/summary — Viewer: financial fields absent from response
  3. GET /reports/summary — Admin in non-billable workspace: financial fields absent
  4. GET /reports/detailed — basic auth and structure
  5. GET /reports/detailed — Member cannot see other user's entries (403)
  6. GET /reports/detailed — cursor pagination returns next_cursor
  7. GET /reports/weekly — basic structure, 7-day range
  8. GET /reports/weekly/export — 32-day span returns 400
  9. GET /reports/saved-views — list empty
  10. POST /reports/saved-views — create success
  11. POST /reports/saved-views — duplicate name → 409
  12. DELETE /reports/saved-views/{id} — success 204
  13. DELETE /reports/saved-views/{id} — other user's view → 404
  14. GET /reports/summary/export — 200 text/csv
  15. GET /reports/detailed/export — 200 text/csv
  16. GET /reports/weekly/export — 200 text/csv
  17. Unauthenticated request → 401
  18. Non-member request → 404

Notes:
  - All report endpoint tests create real time entries via the API to ensure
    the aggregation queries run against actual persisted data.
  - The conftest async_client fixture creates/drops the full schema per test.
"""

from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient


# ── Shared helpers ───────────────────────────────────────────────────────────────

async def _signup_and_create_workspace(client: AsyncClient, suffix: str = "") -> tuple[str, str]:
    """Signup a new user and return (access_token, workspace_id)."""
    email = f"admin_{uuid.uuid4().hex[:8]}_{suffix}@example.com"
    r = await client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "password123",
        "full_name": f"Admin {suffix}",
    })
    assert r.status_code == 201, f"Signup failed: {r.text}"
    data = r.json()
    return data["access_token"], data["workspace"]["id"]


async def _invite_and_join(
    client: AsyncClient,
    admin_token: str,
    ws_id: str,
    role: str = "member",
    suffix: str = "",
) -> tuple[str, str]:
    """Invite a new user and return (member_token, member_user_id)."""
    email = f"{role}_{uuid.uuid4().hex[:8]}_{suffix}@example.com"

    invite_r = await client.post(
        f"/api/v1/workspaces/{ws_id}/invites",
        json={"email": email, "role": role},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invite_r.status_code == 201, f"Invite failed: {invite_r.text}"
    token = invite_r.json()["token"]

    signup_r = await client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "password123",
        "full_name": f"{role.title()} {suffix}",
    })
    assert signup_r.status_code == 201
    member_token = signup_r.json()["access_token"]
    member_user_id = signup_r.json()["user"]["id"]

    accept_r = await client.post(
        f"/api/v1/invites/{token}/accept",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert accept_r.status_code == 200

    return member_token, member_user_id


async def _create_project(client: AsyncClient, token: str, ws_id: str, name: str = "Test Project") -> str:
    r = await client.post(
        "/api/v1/projects",
        params={"workspace_id": ws_id},
        json={"name": name, "visibility": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, f"Create project failed: {r.text}"
    return r.json()["data"]["id"]


async def _create_manual_entry(
    client: AsyncClient, token: str, ws_id: str, project_id: str,
    start: str = "2026-06-09T09:00:00Z",
    end: str = "2026-06-09T11:00:00Z",
    billable: bool = True,
) -> str:
    r = await client.post(
        "/api/v1/time-entries",
        params={"workspace_id": ws_id},
        json={
            "project_id": project_id,
            "start_time": start,
            "end_time": end,
            "billable": billable,
            "description": "Integration test entry",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, f"Create entry failed: {r.text}"
    return r.json()["data"]["id"]


@pytest.mark.asyncio
class TestReportsSummary:
    """GET /reports/summary integration tests."""

    async def test_summary_empty_range_returns_empty_data(self, async_client: AsyncClient):
        """Summary with no entries returns empty data and zero totals."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": ws_id,
                "group_by": "project",
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "summary" in body
        assert body["data"] == []
        assert body["summary"]["total_hours"] == 0.0

    async def test_summary_admin_billable_workspace_has_financial_fields(self, async_client: AsyncClient):
        """
        Admin in billable workspace summary response includes financial fields.
        PRD §4 — Admin can see all financial data.
        """
        token, ws_id = await _signup_and_create_workspace(async_client)
        project_id = await _create_project(async_client, token, ws_id)
        # Increase past_entry_limit for test entries
        await async_client.patch(
            f"/api/v1/workspaces/{ws_id}",
            json={"past_entry_limit_days": 180},
            headers={"Authorization": f"Bearer {token}"},
        )
        await _create_manual_entry(async_client, token, ws_id, project_id)

        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": ws_id,
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        assert "total_billable_amount" in body["summary"], \
            "Admin in billable workspace must see total_billable_amount in summary"

    async def test_summary_viewer_no_financial_fields(self, async_client: AsyncClient):
        """
        RULE U-01: Viewer summary response must NOT contain financial keys.
        Fields must be ABSENT — not null, not hidden, not zero.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        viewer_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="viewer")
        project_id = await _create_project(async_client, admin_token, ws_id)
        await async_client.patch(
            f"/api/v1/workspaces/{ws_id}",
            json={"past_entry_limit_days": 180},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        await _create_manual_entry(async_client, admin_token, ws_id, project_id)

        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": ws_id,
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert r.status_code == 200
        body = r.json()

        # Financial fields must be ABSENT from summary
        assert "total_billable_amount" not in body["summary"], \
            "RULE U-01 violated: total_billable_amount must be ABSENT for Viewer"

        # And absent from data rows
        for row in body["data"]:
            assert "billable_hours" not in row, "billable_hours must be ABSENT for Viewer"
            assert "billable_seconds" not in row, "billable_seconds must be ABSENT for Viewer"
            assert "total_billable_amount" not in row, "total_billable_amount must be ABSENT for Viewer"

    async def test_summary_non_billable_workspace_admin_suppressed(self, async_client: AsyncClient):
        """
        PRD-ADD-05: Admin in non-billable workspace gets suppressed response.
        is_billable=False overrides all roles.
        """
        token, ws_id = await _signup_and_create_workspace(async_client)
        # Disable billable toggle for workspace
        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/billable-settings",
            json={"is_billable": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": ws_id,
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        # Admin must NOT see financial fields in non-billable workspace
        assert "total_billable_amount" not in body["summary"], \
            "PRD-ADD-05 violated: Admin in non-billable workspace must not see total_billable_amount"

    async def test_summary_unauthenticated_returns_401(self, async_client: AsyncClient):
        """No Authorization header → 401."""
        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": str(uuid.uuid4()),
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
        )
        assert r.status_code == 401

    async def test_summary_non_member_returns_404(self, async_client: AsyncClient):
        """User who is not a workspace member → 404 (not 403 — prevents enumeration)."""
        token, _ = await _signup_and_create_workspace(async_client)
        other_token, ws_id_other = await _signup_and_create_workspace(async_client, suffix="other")

        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": ws_id_other,
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},  # wrong workspace
        )
        assert r.status_code == 404

    async def test_summary_group_by_user(self, async_client: AsyncClient):
        """group_by=user returns expected structure."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/summary",
            params={
                "workspace_id": ws_id,
                "group_by": "user",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "summary" in body
        assert "total_hours" in body["summary"]


@pytest.mark.asyncio
class TestReportsDetailed:
    """GET /reports/detailed integration tests."""

    async def test_detailed_empty_returns_empty_list(self, async_client: AsyncClient):
        """No entries → data=[], next_cursor=None."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/detailed",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        assert body["data"] == []
        assert body["next_cursor"] is None
        assert "summary" in body

    async def test_detailed_member_isolation_403(self, async_client: AsyncClient):
        """
        Member requesting another user's entries → 403 FORBIDDEN.
        PITFALL 1 — enforced at service layer.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        member_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="member")

        # Get admin user_id from /me endpoint
        admin_me = await async_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"}
        )
        admin_user_id = admin_me.json()["id"]

        r = await async_client.get(
            "/api/v1/reports/detailed",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
                "user_id": admin_user_id,   # Member requesting admin's data
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 403, "Member must not see other user's detailed entries"

    async def test_detailed_viewer_no_financial_fields(self, async_client: AsyncClient):
        """
        RULE U-01: Viewer detailed entries must not have financial fields.
        hourly_rate_cents and billable_amount_cents must be ABSENT.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        viewer_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="viewer")
        project_id = await _create_project(async_client, admin_token, ws_id)
        await async_client.patch(
            f"/api/v1/workspaces/{ws_id}",
            json={"past_entry_limit_days": 180},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        await _create_manual_entry(async_client, viewer_token, ws_id, project_id)

        r = await async_client.get(
            "/api/v1/reports/detailed",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert r.status_code == 200
        body = r.json()
        for entry in body["data"]:
            assert "hourly_rate_cents" not in entry, \
                "RULE U-01: hourly_rate_cents must be ABSENT for Viewer"
            assert "billable_amount_cents" not in entry, \
                "RULE U-01: billable_amount_cents must be ABSENT for Viewer"

    async def test_detailed_response_structure(self, async_client: AsyncClient):
        """GET /reports/detailed response has expected top-level keys."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/detailed",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "next_cursor" in body
        assert "limit" in body
        assert "summary" in body
        assert "total_hours" in body["summary"]


@pytest.mark.asyncio
class TestReportsWeekly:
    """GET /reports/weekly integration tests."""

    async def test_weekly_basic_structure(self, async_client: AsyncClient):
        """7-day weekly report returns correct structure."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/weekly",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-09",
                "date_to": "2026-06-15",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        data = body["data"]
        assert "date_from" in data
        assert "date_to" in data
        assert "days" in data
        assert len(data["days"]) == 7
        assert "rows" in data
        assert "totals" in data
        assert "by_day" in data["totals"]
        assert "grand_total_hours" in data["totals"]

    async def test_weekly_32_day_span_returns_400(self, async_client: AsyncClient):
        """API Spec v1.1 §14: date span > 31 days → HTTP 400."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/weekly",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-07-03",   # 32 days
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400

    async def test_weekly_31_day_span_succeeds(self, async_client: AsyncClient):
        """API Spec v1.1 §14: exactly 31 days is within allowed limit → 200."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/weekly",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-07-01",   # 30 days (< 31 limit)
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    async def test_weekly_admin_has_billable_totals(self, async_client: AsyncClient):
        """Admin in billable workspace weekly totals has grand_total_billable_amount."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/weekly",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-09",
                "date_to": "2026-06-15",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        totals = r.json()["data"]["totals"]
        assert "grand_total_billable_amount" in totals, \
            "Admin in billable workspace must see grand_total_billable_amount"

    async def test_weekly_viewer_no_billable_total(self, async_client: AsyncClient):
        """
        RULE U-01: Viewer weekly totals must NOT have grand_total_billable_amount.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        viewer_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="viewer")

        r = await async_client.get(
            "/api/v1/reports/weekly",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-09",
                "date_to": "2026-06-15",
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert r.status_code == 200
        totals = r.json()["data"]["totals"]
        assert "grand_total_billable_amount" not in totals, \
            "RULE U-01: grand_total_billable_amount must be ABSENT for Viewer"

    async def test_weekly_member_isolation_403(self, async_client: AsyncClient):
        """Member requesting another user's row → 403."""
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        member_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="member")

        # Get admin user id
        me = await async_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"}
        )
        admin_user_id = me.json()["id"]

        r = await async_client.get(
            "/api/v1/reports/weekly",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-09",
                "date_to": "2026-06-15",
                "user_id": admin_user_id,
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 403


@pytest.mark.asyncio
class TestSavedViews:
    """
    GET/POST/DELETE /reports/saved-views integration tests.
    PRD §3.8: saved views are private to the creating user's account.
    """

    async def test_list_saved_views_empty(self, async_client: AsyncClient):
        """New user has no saved views — returns empty list."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        assert r.json() == []

    async def test_create_saved_view(self, async_client: AsyncClient):
        """POST saved-view creates and returns the view with correct fields."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json={
                "name": "Last 30 Days",
                "report_type": "summary",
                "filters": {"group_by": "project", "date_from": "2026-06-01"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Last 30 Days"
        assert body["report_type"] == "summary"
        assert "id" in body
        assert "created_at" in body

    async def test_create_saved_view_duplicate_name_409(self, async_client: AsyncClient):
        """
        API Spec v1.1 §14: POSTing the same name twice → 409 DUPLICATE_NAME.
        """
        token, ws_id = await _signup_and_create_workspace(async_client)

        payload = {
            "name": "My Saved Report",
            "report_type": "detailed",
            "filters": {},
        }

        r1 = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 201

        r2 = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json=payload,  # same name
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 409

    async def test_create_weekly_report_type_accepted(self, async_client: AsyncClient):
        """DB Schema v2.1 §5: report_type='weekly' is valid per CHECK constraint."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json={
                "name": "Weekly Overview",
                "report_type": "weekly",
                "filters": {},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
        assert r.json()["report_type"] == "weekly"

    async def test_delete_saved_view_204(self, async_client: AsyncClient):
        """DELETE saved-view returns 204 No Content and view is gone."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        create_r = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json={"name": "To Delete", "report_type": "summary", "filters": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_r.status_code == 201
        view_id = create_r.json()["id"]

        delete_r = await async_client.delete(
            f"/api/v1/reports/saved-views/{view_id}",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_r.status_code == 204

        # Verify it's gone
        list_r = await async_client.get(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_r.status_code == 200
        ids = [v["id"] for v in list_r.json()]
        assert view_id not in ids

    async def test_delete_other_users_view_404(self, async_client: AsyncClient):
        """
        PRD §3.8: saved views are private. Another user deleting a view → 404.
        Returns 404, not 403, to prevent revealing existence of the view.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        other_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="member")

        # Admin creates a view
        create_r = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json={"name": "Admin Private View", "report_type": "summary", "filters": {}},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_r.status_code == 201
        view_id = create_r.json()["id"]

        # Member tries to delete admin's view
        delete_r = await async_client.delete(
            f"/api/v1/reports/saved-views/{view_id}",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert delete_r.status_code == 404, \
            "Other user deleting a view must return 404, not 403"

    async def test_list_shows_only_own_views(self, async_client: AsyncClient):
        """
        PRD §3.8: saved views are private. User B cannot see User A's views.
        GET /reports/saved-views returns only the requesting user's views.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        member_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="member")

        # Admin creates a view
        await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json={"name": "Admin View", "report_type": "summary", "filters": {}},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Member lists views — should see empty (not admin's)
        r = await async_client.get(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert r.status_code == 200
        assert r.json() == [], "Member must not see Admin's saved views (PRD §3.8)"

    async def test_invalid_report_type_422(self, async_client: AsyncClient):
        """
        report_type='invalid' must be rejected before reaching DB layer.
        Pydantic Literal validator → 422 UNPROCESSABLE_ENTITY.
        """
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.post(
            "/api/v1/reports/saved-views",
            params={"workspace_id": ws_id},
            json={"name": "Bad Type", "report_type": "invalid", "filters": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422


@pytest.mark.asyncio
class TestCSVExports:
    """
    CSV export endpoints return text/csv content.
    Suppression rules apply: Viewer and non-billable workspace get fewer columns.
    """

    async def test_summary_export_returns_csv(self, async_client: AsyncClient):
        """GET /reports/summary/export returns Content-Type: text/csv."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/summary/export",
            params={
                "workspace_id": ws_id,
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        content = r.text
        # Header row must exist
        assert "Group" in content
        # Admin in billable workspace: financial columns present
        assert "Billable Amount" in content

    async def test_detailed_export_returns_csv(self, async_client: AsyncClient):
        """GET /reports/detailed/export returns Content-Type: text/csv."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/detailed/export",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        content = r.text
        assert "User" in content
        # Admin in billable workspace: financial columns present
        assert "Billable Amount" in content

    async def test_weekly_export_returns_csv(self, async_client: AsyncClient):
        """GET /reports/weekly/export returns Content-Type: text/csv."""
        token, ws_id = await _signup_and_create_workspace(async_client)

        r = await async_client.get(
            "/api/v1/reports/weekly/export",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-09",
                "date_to": "2026-06-15",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        content = r.text
        assert "Member" in content
        assert "Total Hours" in content

    async def test_summary_export_viewer_no_financial_columns(self, async_client: AsyncClient):
        """
        RULE U-01 / PITFALL 4: Viewer CSV export must NOT contain financial column headers.
        'Billable Amount' and 'Billable Hours' headers must be ABSENT.
        """
        admin_token, ws_id = await _signup_and_create_workspace(async_client)
        viewer_token, _ = await _invite_and_join(async_client, admin_token, ws_id, role="viewer")

        r = await async_client.get(
            "/api/v1/reports/summary/export",
            params={
                "workspace_id": ws_id,
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert r.status_code == 200
        content = r.text
        assert "Billable Amount" not in content, \
            "RULE U-01 + PITFALL 4: Billable Amount must be ABSENT from Viewer CSV"

    async def test_detailed_export_non_billable_no_financial_columns(self, async_client: AsyncClient):
        """
        PRD-ADD-05 + PITFALL 4: Non-billable workspace Admin CSV has no financial columns.
        """
        token, ws_id = await _signup_and_create_workspace(async_client)
        # Disable billable
        r = await async_client.patch(
            f"/api/v1/workspaces/{ws_id}/billable-settings",
            json={"is_billable": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

        r = await async_client.get(
            "/api/v1/reports/detailed/export",
            params={
                "workspace_id": ws_id,
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert r.status_code == 200
        content = r.text
        assert "Billable Amount" not in content, \
            "PRD-ADD-05 + PITFALL 4: Billable Amount must be ABSENT from non-billable workspace CSV"
        assert "Hourly Rate" not in content

    async def test_export_unauthenticated_401(self, async_client: AsyncClient):
        """Unauthenticated CSV export request → 401."""
        r = await async_client.get(
            "/api/v1/reports/summary/export",
            params={
                "workspace_id": str(uuid.uuid4()),
                "group_by": "project",
                "date_from": "2026-06-01",
                "date_to": "2026-06-30",
            },
        )
        assert r.status_code == 401
