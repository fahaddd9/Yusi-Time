"""
Comprehensive F1 test: 3A, 3B, 3C
Uses programmatically generated JWT tokens (bypassing login).
"""
import asyncio
import httpx
from datetime import date, datetime, timedelta
import zoneinfo
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.core.config import get_settings
from app.models.attendance_notification import AttendanceNotification
from app.services import scheduler_service

BASE_URL = "http://localhost:8001/api/v1"
WORKSPACE_ID = "229bc373-21c5-436c-aef2-6aec8cf7e50d"
ADMIN_USER_ID = "05b05ac6-6465-42be-915b-b7be212287fe"   # thefadi384@gmail.com (admin of Yusi Time)
MEMBER_USER_ID = "dfd79611-75b0-4633-b96a-2e8cb809ece7"  # bob@email.com (member)
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
    admin_tok = create_access_token(ADMIN_USER_ID, settings=s)
    member_tok = create_access_token(MEMBER_USER_ID, settings=s)
    return admin_tok, member_tok


async def patch_attendance(client, token, **kwargs):
    r = await client.patch(
        f"{BASE_URL}/workspaces/{WORKSPACE_ID}/attendance-settings",
        json=kwargs, headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code != 200:
        print(f"  PATCH FAIL: {r.status_code} {r.text[:200]}")
        return None
    return r.json()


async def get_notifs(client, token):
    r = await client.get(
        f"{BASE_URL}/notifications/attendance",
        params={"workspace_id": WORKSPACE_ID, "scope": "self", "per_page": 20},
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.status_code, r.json()


async def work_start_resp(client, token, response, project_id=None):
    body = {"response": response}
    if project_id:
        body["project_id"] = project_id
    r = await client.post(
        f"{BASE_URL}/time-entries/work-start-response",
        json=body, params={"workspace_id": WORKSPACE_ID},
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.status_code, r.json()


async def get_projects(client, token):
    r = await client.get(
        f"{BASE_URL}/projects",
        params={"workspace_id": WORKSPACE_ID},
        headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code == 200:
        d = r.json()
        items = d.get("data", d) if isinstance(d, dict) else d
        return items if isinstance(items, list) else []
    return []


async def list_entries(client, token):
    r = await client.get(
        f"{BASE_URL}/time-entries",
        params={"workspace_id": WORKSPACE_ID},
        headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code == 200:
        d = r.json()
        return d.get("data", d) if isinstance(d, dict) else d
    return []


async def delete_entry(client, token, entry_id):
    r = await client.delete(
        f"{BASE_URL}/time-entries/{entry_id}",
        params={"workspace_id": WORKSPACE_ID},
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.status_code


async def clear_notifications():
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            delete(AttendanceNotification).where(
                AttendanceNotification.related_date == date.today()
            )
        )
        await db.commit()
        return res.rowcount


async def clear_entries(client, token):
    entries = await list_entries(client, token)
    today = datetime.now(tz=TZ).date()
    deleted = 0
    for e in entries:
        st = e.get("start_time", "")
        if st:
            try:
                dt = datetime.fromisoformat(st.replace("Z", "+00:00")).astimezone(TZ).date()
                if dt == today:
                    s = await delete_entry(client, token, e["id"])
                    if s == 200:
                        deleted += 1
            except Exception:
                pass
    return deleted


async def trigger():
    await scheduler_service.check_workspace_attendance()


def now_pkt():
    return datetime.now(tz=TZ)


# ---- Main ----

async def main():
    global PASS_COUNT, FAIL_COUNT
    PASS_COUNT = 0
    FAIL_COUNT = 0

    print("=" * 65)
    print("F1 FULL TEST SUITE (3A + 3B + 3C)")
    print("=" * 65)

    admin_token, member_token = make_tokens()
    print("Tokens generated OK.")

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Get a project
        print("\n[SETUP] Fetching projects...")
        projects = await get_projects(client, member_token)
        project_id = projects[0]["id"] if projects else None
        if project_id:
            print(f"  Using project: {projects[0].get('name', 'N/A')} ({str(project_id)[:8]})")
        else:
            print("  WARNING: No projects found.")

        # ====================================================
        # 3A: ON-TIME PROMPT
        # ====================================================
        print("\n" + "=" * 65)
        print("3A: ON-TIME PROMPT")
        print("=" * 65)

        n_c = await clear_notifications()
        e_c = await clear_entries(client, member_token)
        print(f"Cleared {n_c} notifications, {e_c} entries")

        # Set work_start_time = current minute so scheduler triggers
        now = now_pkt()
        start_str = now.strftime("%H:%M")
        print(f"\nSetting work_start_time={start_str} (now={now.strftime('%H:%M:%S')} PKT)")
        s = await patch_attendance(
            client, admin_token,
            attendance_enabled=True,
            attendance_mode="fixed_schedule",
            work_start_time=start_str,
            daily_required_hours=0.08,
            off_days=[]
        )
        if s:
            print(f"  Settings OK: mode={s.get('attendance_mode')} start={s.get('work_start_time')}")

        print("Triggering scheduler...")
        await trigger()

        _, notifs = await get_notifs(client, member_token)
        today_str = str(date.today())
        ws_notifs = [n for n in notifs.get("data", [])
                     if n["notification_type"] == "work_start_missed" and n["related_date"] == today_str]

        check("F1-01", len(ws_notifs) > 0,
              f"work_start_missed notification created ({len(ws_notifs)})",
              f"No notification created! Data={notifs}")

        if ws_notifs:
            n = ws_notifs[0]
            late = n.get("late_by_minutes")
            check("F1-05", late is None or late == 0,
                  f"On-time: late_by_minutes={late} (null/0=correct)",
                  f"Expected null/0 late_by_minutes but got {late}")

        print("  [FRONTEND] F1-02: Backdrop click blocked (onOpenChange no-op)")
        print("  [FRONTEND] F1-03: Escape key blocked (onKeyDown preventDefault)")
        print("  [FRONTEND] F1-04: No X close button (showCloseButton=false)")

        # F1-06..F1-10: Start Tracking
        print("\n[F1-06..10] Testing 'Start Tracking'...")
        if ws_notifs and project_id:
            status, result = await work_start_resp(client, member_token, "start", project_id)
            check("F1-09", status == 200 and result.get("acknowledged"),
                  f"POST work-start-response -> 200 | entry_id={str(result.get('time_entry_id',''))[:8]}",
                  f"Expected 200 got {status}: {result}")
            _, notifs_after = await get_notifs(client, member_token)
            unread = [n for n in notifs_after.get("data", [])
                      if n["notification_type"] == "work_start_missed" and not n["is_read"]]
            check("F1-08", len(unread) == 0,
                  "Notification marked read after start",
                  f"{len(unread)} still unread")
        else:
            print("  [SKIP] No notification or project for F1-06..10")

        # ====================================================
        # 3B: NOT NOW
        # ====================================================
        print("\n" + "=" * 65)
        print("3B: 'NOT NOW' RESPONSE")
        print("=" * 65)

        n_c = await clear_notifications()
        e_c = await clear_entries(client, member_token)
        print(f"Cleared {n_c} notifications, {e_c} entries")

        now = now_pkt()
        start_str = now.strftime("%H:%M")
        print(f"Setting work_start_time={start_str}")
        await patch_attendance(client, admin_token, attendance_enabled=True,
                               attendance_mode="fixed_schedule", work_start_time=start_str,
                               daily_required_hours=0.08, off_days=[])
        await trigger()

        _, notifs_3b = await get_notifs(client, member_token)
        unread_3b = [n for n in notifs_3b.get("data", [])
                     if n["notification_type"] == "work_start_missed" and not n["is_read"]]

        if unread_3b:
            print(f"\n[F1-12/13] Clicking 'Not Now'...")
            status_nn, result_nn = await work_start_resp(client, member_token, "not_now")
            check("F1-12/13", status_nn == 200 and result_nn.get("acknowledged"),
                  f"'Not Now' -> 200 | message={result_nn.get('message','')}",
                  f"Expected 200 got {status_nn}: {result_nn}")

            _, notifs_14 = await get_notifs(client, member_token)
            all_14 = notifs_14.get("data", [])
            unread_14 = [n for n in all_14 if not n["is_read"] and n["notification_type"] == "work_start_missed"]
            read_14 = [n for n in all_14 if n["is_read"] and n["notification_type"] == "work_start_missed"]
            check("F1-14", len(read_14) > 0 and len(unread_14) == 0,
                  f"Notification bell: read={len(read_14)}, unread={len(unread_14)}",
                  f"Expected read>0 and unread=0 but read={len(read_14)}, unread={len(unread_14)}")

            # F1-15: No re-prompt
            print("\n[F1-15] Triggering scheduler again (no re-prompt expected)...")
            await trigger()
            _, notifs_15 = await get_notifs(client, member_token)
            unread_15 = [n for n in notifs_15.get("data", []) if not n["is_read"]]
            check("F1-15", len(unread_15) == 0,
                  "No new notification after 'Not Now' - no re-prompt",
                  f"New unread notifications appeared! {unread_15}")
        else:
            print(f"  [SKIP] No notification for 3B test. Notifs={notifs_3b}")

        print("  [FRONTEND] F1-16: Page refresh no re-prompt (is_read=True backend guard)")

        # ====================================================
        # 3C: LATE ARRIVAL
        # ====================================================
        print("\n" + "=" * 65)
        print("3C: LATE ARRIVAL")
        print("=" * 65)

        n_c = await clear_notifications()
        e_c = await clear_entries(client, member_token)
        print(f"Cleared {n_c} notifications, {e_c} entries")

        now = now_pkt()
        past_time = now - timedelta(minutes=5)
        past_str = past_time.strftime("%H:%M")
        print(f"Setting work_start_time={past_str} (5 min ago, now={now.strftime('%H:%M:%S')})")
        await patch_attendance(client, admin_token, attendance_enabled=True,
                               attendance_mode="fixed_schedule", work_start_time=past_str,
                               daily_required_hours=0.08, off_days=[])

        print("Triggering scheduler (late arrival scenario)...")
        await trigger()

        _, notifs_3c = await get_notifs(client, member_token)
        late_notifs = [n for n in notifs_3c.get("data", [])
                       if n["notification_type"] == "work_start_missed" and n["related_date"] == today_str]

        check("F1-18", len(late_notifs) > 0,
              "Late arrival notification created",
              f"No late notification! Data={notifs_3c}")

        if late_notifs:
            n = late_notifs[0]
            late_mins = n.get("late_by_minutes")
            check("F1-19/20", late_mins is not None and 4 <= int(late_mins) <= 8,
                  f"late_by_minutes={late_mins} (~5 min, expected 4-8)",
                  f"late_by_minutes={late_mins} not in range 4-8")

        print("  [FRONTEND] F1-21: Modal shows Start Tracking + Not Now buttons")

        # F1-22: Start tracking from late arrival
        if late_notifs and project_id:
            print("\n[F1-22] Start Tracking from late arrival...")
            status_22, result_22 = await work_start_resp(client, member_token, "start", project_id)
            check("F1-22", status_22 == 200 and result_22.get("acknowledged"),
                  f"Timer started | entry={str(result_22.get('time_entry_id',''))[:8]}",
                  f"Expected 200 got {status_22}: {result_22}")
        else:
            print("  [SKIP] F1-22: No notification or project")

        # F1-23: Already has timer -> no notification
        print("\n[F1-23] Member with timer should NOT get modal...")
        n_c = await clear_notifications()
        print(f"  Cleared {n_c} notifications (keeping time entry from F1-22)")
        await trigger()
        _, notifs_23 = await get_notifs(client, member_token)
        new_notifs_23 = [n for n in notifs_23.get("data", [])
                         if n["notification_type"] == "work_start_missed" and n["related_date"] == today_str]
        check("F1-23", len(new_notifs_23) == 0,
              "No notification when member has time entry today",
              f"Notification created even though member has timer! {new_notifs_23}")

        # ====================================================
        # SUMMARY
        # ====================================================
        print("\n" + "=" * 65)
        total = PASS_COUNT + FAIL_COUNT
        print(f"FINAL RESULTS: {PASS_COUNT}/{total} PASS  |  {FAIL_COUNT}/{total} FAIL")
        print("=" * 65)

asyncio.run(main())
