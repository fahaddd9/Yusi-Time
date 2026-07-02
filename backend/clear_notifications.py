import asyncio
from datetime import date
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.attendance_notification import AttendanceNotification

async def main():
    async with AsyncSessionLocal() as db:
        stmt = delete(AttendanceNotification).where(
            AttendanceNotification.related_date == date(2026, 6, 26)
        )
        result = await db.execute(stmt)
        await db.commit()
        print(f"Deleted {result.rowcount} notifications for today.")

asyncio.run(main())
