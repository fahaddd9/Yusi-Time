import asyncio
from app.core.database import AsyncSessionLocal
from app.models.time_entry import TimeEntry
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TimeEntry).order_by(TimeEntry.created_at.desc()).limit(10))
        entries = result.scalars().all()
        print("Found entries:", len(entries))
        for e in entries:
            print(f"ID: {e.id}, User: {e.user_id}, Start: {e.start_time}, End: {e.end_time}, Duration: {e.duration_seconds}, Proj: {e.project_id}")

asyncio.run(run())
