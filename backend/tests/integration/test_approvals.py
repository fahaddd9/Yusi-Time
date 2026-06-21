from httpx import AsyncClient
import pytest
import uuid

@pytest.mark.asyncio
class TestApprovalsIntegration:

    async def setup_test_users_and_workspace(self, async_client: AsyncClient):
        admin_email = f"admin_{uuid.uuid4()}@example.com"
        member_email = f"member_{uuid.uuid4()}@example.com"
        
        # Admin signup
        r = await async_client.post("/api/v1/auth/signup", json={
            "email": admin_email, "password": "password123", "full_name": "Admin"
        })
        admin_token = r.json()["access_token"]
        ws_id = r.json()["workspace"]["id"]
        
        # Enable workflow and increase past entry limit for testing old dates
        await async_client.patch(f"/api/v1/workspaces/{ws_id}", json={
            "approval_workflow_enabled": True,
            "past_entry_limit_days": 90
        }, headers={"Authorization": f"Bearer {admin_token}"})

        # Create project
        r = await async_client.post(f"/api/v1/projects", params={"workspace_id": ws_id}, json={
            "name": "Test Project", "visibility": "public"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        project_id = r.json()["data"]["id"]

        # Admin creates invite
        invite_resp = await async_client.post(
            f"/api/v1/workspaces/{ws_id}/invites",
            json={"email": member_email, "role": "member"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        token = invite_resp.json()["token"]

        # Member signup
        r = await async_client.post("/api/v1/auth/signup", json={
            "email": member_email, "password": "password123", "full_name": "Member"
        })
        member_token = r.json()["access_token"]

        # Member accepts invite
        await async_client.post(
            f"/api/v1/invites/{token}/accept",
            headers={"Authorization": f"Bearer {member_token}"},
        )

        return admin_token, member_token, ws_id, project_id

    async def test_full_approve_flow(self, async_client: AsyncClient):
        admin_token, member_token, ws_id, project_id = await self.setup_test_users_and_workspace(async_client)

        # Member creates manual time entry
        r = await async_client.post("/api/v1/time-entries", params={"workspace_id": ws_id}, json={
            "project_id": project_id,
            "start_time": "2026-05-18T09:00:00Z",
            "end_time": "2026-05-18T10:00:00Z",
            "description": "Test work"
        }, headers={"Authorization": f"Bearer {member_token}"})
        assert r.status_code == 201

        # Member submits week
        r = await async_client.post("/api/v1/approvals/submit", params={"workspace_id": ws_id}, json={
            "week_start": "2026-05-18"
        }, headers={"Authorization": f"Bearer {member_token}"})
        assert r.status_code == 201
        sub_id = r.json()["data"]["id"]

        # Admin approves submission
        r = await async_client.post(f"/api/v1/approvals/{sub_id}/approve", params={"workspace_id": ws_id}, headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "approved"

    async def test_full_reject_resubmit_flow(self, async_client: AsyncClient):
        admin_token, member_token, ws_id, project_id = await self.setup_test_users_and_workspace(async_client)

        # Member creates manual time entry
        r = await async_client.post("/api/v1/time-entries", params={"workspace_id": ws_id}, json={
            "project_id": project_id,
            "start_time": "2026-05-18T09:00:00Z",
            "end_time": "2026-05-18T10:00:00Z",
            "description": "Test work"
        }, headers={"Authorization": f"Bearer {member_token}"})
        
        # Submit
        r = await async_client.post("/api/v1/approvals/submit", params={"workspace_id": ws_id}, json={
            "week_start": "2026-05-18"
        }, headers={"Authorization": f"Bearer {member_token}"})
        sub_id = r.json()["data"]["id"]

        # Admin rejects
        r = await async_client.post(f"/api/v1/approvals/{sub_id}/reject", params={"workspace_id": ws_id}, json={
            "note": "Needs more detail"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "rejected"

        # Member resubmits
        r = await async_client.post("/api/v1/approvals/submit", params={"workspace_id": ws_id}, json={
            "week_start": "2026-05-18"
        }, headers={"Authorization": f"Bearer {member_token}"})
        assert r.status_code == 201

    async def test_member_cannot_edit_pending(self, async_client: AsyncClient):
        admin_token, member_token, ws_id, project_id = await self.setup_test_users_and_workspace(async_client)

        # Create entry
        r = await async_client.post("/api/v1/time-entries", params={"workspace_id": ws_id}, json={
            "project_id": project_id,
            "start_time": "2026-05-18T09:00:00Z",
            "end_time": "2026-05-18T10:00:00Z",
            "description": "Test work"
        }, headers={"Authorization": f"Bearer {member_token}"})
        entry_id = r.json()["data"]["id"]

        # Submit
        await async_client.post("/api/v1/approvals/submit", params={"workspace_id": ws_id}, json={
            "week_start": "2026-05-18"
        }, headers={"Authorization": f"Bearer {member_token}"})

        # Member attempts to edit pending entry
        r = await async_client.patch(f"/api/v1/time-entries/{entry_id}", params={"workspace_id": ws_id}, json={
            "description": "Attempt edit"
        }, headers={"Authorization": f"Bearer {member_token}"})
        assert r.status_code == 403

    async def test_admin_can_edit_pending(self, async_client: AsyncClient):
        admin_token, member_token, ws_id, project_id = await self.setup_test_users_and_workspace(async_client)

        # Create entry
        r = await async_client.post("/api/v1/time-entries", params={"workspace_id": ws_id}, json={
            "project_id": project_id,
            "start_time": "2026-05-18T09:00:00Z",
            "end_time": "2026-05-18T10:00:00Z",
            "description": "Test work"
        }, headers={"Authorization": f"Bearer {member_token}"})
        entry_id = r.json()["data"]["id"]

        # Submit
        await async_client.post("/api/v1/approvals/submit", params={"workspace_id": ws_id}, json={
            "week_start": "2026-05-18"
        }, headers={"Authorization": f"Bearer {member_token}"})

        # Admin edits pending entry
        r = await async_client.patch(f"/api/v1/time-entries/{entry_id}", params={"workspace_id": ws_id}, json={
            "description": "Admin edited"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
