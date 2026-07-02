import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text('SELECT id, workspace_id, user_id, recipient_user_id, notification_type, related_date FROM attendance_notifications ORDER BY created_at DESC LIMIT 20'))
        rows = r.fetchall()
        print('Notifications in DB:')
        for row in rows:
            print(row)

asyncio.run(main())
