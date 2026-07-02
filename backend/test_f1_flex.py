"""
Comprehensive F1 Flexible Hours test: 3D
Uses programmatically generated JWT tokens.
"""
import asyncio
import httpx
from datetime import date, datetime, timedelta
import zoneinfo
from sqlalchemy import delete
from sqlalchemy.sql import text
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.core.config import get_settings
from app.models.attendance_notification import AttendanceNotification
from app.models.time_entry import TimeEntry
from app.services import scheduler_service

BASE_URL = "http://localhost:8001/api/v1"
WORKSPACE_ID = "229bc373-21c5-436c-aef2-6aec8cf7e50d"
ADMIN_USER_ID = "05b05ac6-6465-42be-915b-b7be212287fe"   # admin
MEMBER_USER_ID = "dfd79611-75b0-4633-b96a-2e8cb809ece7"  # bob
TZ = zoneinfo.ZoneInfo("Asia/Karachi")

PASS_COUNT = 0
FAIL_COUNT = 0

def check(test_id, condition, msg_pass, msg_fail):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  [PASS] {test_id}: {msg_pass}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] {test_id}: {msg_fail}")
    return condition

def make_tokens():
    s = get_settings()
    return create_access_token(ADMIN_USER_ID, settings=s), create_access_token(MEMBER_USER_ID, settings=s)

async def patch_attendance(client, token, **kwargs):
    r = await client.patch(
        f"{BASE_URL}/workspaces/{WORKSPACE_ID}/attendance-settings",
        json=kwargs, headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code != 200:
        print(f"  PATCH FAIL: {r.status_code} {r.text[:200]}")

async def clear_db():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(AttendanceNotification))
        
        # Delete time entries for today
        today = date.today()
        dt_start = datetime.combine(today, datetime.min.time())
        await db.execute(delete(TimeEntry).where(TimeEntry.start_time >= dt_start))
        await db.commit()

async def create_time_entry(client, token):
    # Get a project that Bob has access to
    pr = await client.get(
        f"{BASE_URL}/projects?workspace_id={WORKSPACE_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )
    pid = pr.json()["data"][0]["id"]
    
    r = await client.post(
        f"{BASE_URL}/time-entries/start?workspace_id={WORKSPACE_ID}",
        json={"start_time": datetime.now(TZ).isoformat(), "project_id": str(pid)},
        headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code != 201:
        print(f"  CREATE TE FAIL: {r.status_code} {r.text[:200]}")
    return r.json()

async def stop_time_entry(client, token, entry_id):
    r = await client.post(
        f"{BASE_URL}/time-entries/{entry_id}/stop",
        json={"end_time": datetime.now(TZ).isoformat()},
        headers={"Authorization": f"Bearer {token}"}
    )

async def main():
    admin_token, member_token = make_tokens()
    
    async with httpx.AsyncClient() as client:
        print("\n--- 3D Flexible Hours Mode Prompt ---")
        
        await clear_db()
        
        # F1-24: Switch mode to Flexible Hours, set time 2 mins from now
        now = datetime.now(TZ)
        start_time_dt = now + timedelta(minutes=-5) # Setting it 5 mins ago so scheduler triggers immediately
        
        await patch_attendance(
            client, admin_token,
            attendance_enabled=True,
            attendance_mode="flexible_hours",
            work_start_time=start_time_dt.strftime("%H:%M")
        )
        
        # F1-25: Wait for work_start_time to arrive (run scheduler)
        await scheduler_service.check_workspace_attendance()
        
        # Check if notification was created
        r = await client.get(
            f"{BASE_URL}/notifications/attendance?workspace_id={WORKSPACE_ID}",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        data = r.json()
        
        check("F1-25", len(data["data"]) == 1, "Notification created for flexible hours.", "No notification created.")
        
        # F1-26 & 27: Read modal copy -> late_by_minutes MUST be null
        if len(data["data"]) > 0:
            notif = data["data"][0]
            check("F1-26/27", notif["notification_type"] == "flexible_reminder_missed" and notif["late_by_minutes"] is None,
                  "Type is flexible_reminder_missed and late_by_minutes is null.", f"Unexpected values: {notif}")
        
        print("\n--- Testing F1-28/29 (Reset + Entry Logged) ---")
        await clear_db()
        
        # F1-28: Log a small time entry BEFORE work_start_time arrives
        te = await create_time_entry(client, member_token)
        await stop_time_entry(client, member_token, te["id"])
        
        # F1-29: Wait for work_start_time to arrive (run scheduler)
        await scheduler_service.check_workspace_attendance()
            
        r = await client.get(
            f"{BASE_URL}/notifications/attendance?workspace_id={WORKSPACE_ID}",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        data = r.json()
        
        check("F1-29", len(data["data"]) == 0, "No notification created because time was already logged.", f"Notification unexpectedly created: {data['data']}")
        
        print(f"\nRESULTS: {PASS_COUNT} Passed, {FAIL_COUNT} Failed")

if __name__ == "__main__":
    asyncio.run(main())
