import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT id, related_date, is_read FROM attendance_notifications WHERE user_id='ef09d5af-818c-4310-8d52-7aec4bc9946d'"))
        for row in r.fetchall():
            print(row)

asyncio.run(main())
