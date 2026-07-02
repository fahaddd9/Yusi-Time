import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
async def run():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT u.id, u.email, wm.role FROM users u JOIN workspace_members wm ON wm.user_id = u.id WHERE wm.workspace_id = '229bc373-21c5-436c-aef2-6aec8cf7e50d'"))
        rows = r.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Email: {row[1]}, Role: {row[2]}")
asyncio.run(run())
