import asyncio
from datetime import datetime, timezone
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.time_entry import TimeEntry
from app.models.attendance_notification import AttendanceNotification

async def reset_todays_data():
    async with AsyncSessionLocal() as db:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Delete time entries
        await db.execute(delete(TimeEntry).where(TimeEntry.start_time >= today))
        
        # Delete attendance notifications (by checking created_at)
        await db.execute(delete(AttendanceNotification).where(AttendanceNotification.created_at >= today))
        
        await db.commit()
        print("Reset complete. Today's time entries and notifications deleted.")

if __name__ == "__main__":
    asyncio.run(reset_todays_data())
