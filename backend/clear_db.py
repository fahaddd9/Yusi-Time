import asyncio
from sqlalchemy import text, delete
from datetime import date, datetime
from app.core.database import AsyncSessionLocal
from app.models.time_entry import TimeEntry
from app.models.attendance_notification import AttendanceNotification

async def main():
    async with AsyncSessionLocal() as db:
        # Delete test time entries for today
        today = date.today()
        # Convert date to datetime for timestamp comparison
        dt_start = datetime.combine(today, datetime.min.time())
        res_te = await db.execute(delete(TimeEntry).where(TimeEntry.start_time >= dt_start))
        
        # Delete today's notifications again
        res_notif = await db.execute(delete(AttendanceNotification).where(AttendanceNotification.related_date == today))
        
        await db.commit()
        print(f'Deleted {res_te.rowcount} time entries and {res_notif.rowcount} notifications for today.')

asyncio.run(main())
