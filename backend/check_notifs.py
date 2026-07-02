import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text('SELECT user_id, notification_type, is_read, related_date FROM attendance_notifications WHERE related_date = CURRENT_DATE'))
        rows = r.fetchall()
        print('Notifications Today:')
        for row in rows:
            print(row)

asyncio.run(main())
