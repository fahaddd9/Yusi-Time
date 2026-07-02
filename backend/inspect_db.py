import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT email, id FROM users ORDER BY created_at LIMIT 20"))
        print("USERS:")
        for row in r.fetchall():
            print(" ", row[0], "|", row[1])
        
        r2 = await db.execute(text("SELECT name, id, attendance_enabled, work_start_time, default_timezone, attendance_mode, off_days FROM workspaces LIMIT 10"))
        print("WORKSPACES:")
        for row in r2.fetchall():
            print(" ", row[0], "|", str(row[1])[:8], "| enabled:", row[2], "| start:", row[3], "| tz:", row[4], "| mode:", row[5], "| off_days:", row[6])
        
        r3 = await db.execute(text("SELECT workspace_id, user_id, role FROM workspace_members LIMIT 30"))
        print("MEMBERS:")
        for row in r3.fetchall():
            print("  ws:", str(row[0])[:8], "| user:", str(row[1])[:8], "| role:", row[2])
        
        r4 = await db.execute(text("SELECT id, workspace_id, recipient_user_id, notification_type, related_date, is_read, late_by_minutes FROM attendance_notifications ORDER BY created_at DESC LIMIT 10"))
        print("NOTIFICATIONS:")
        for row in r4.fetchall():
            print("  id:", str(row[0])[:8], "| type:", row[3], "| date:", row[4], "| read:", row[5], "| late_min:", row[6])

asyncio.run(main())
