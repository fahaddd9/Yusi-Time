import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text('SELECT id, user_id, start_time FROM time_entries WHERE DATE(start_time) = CURRENT_DATE'))
        rows = r.fetchall()
        print('Time Entries Today:')
        for row in rows:
            print(row)

asyncio.run(main())
