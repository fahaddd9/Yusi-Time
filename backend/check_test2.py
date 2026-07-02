import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT role FROM workspace_members WHERE workspace_id='229bc373-21c5-436c-aef2-6aec8cf7e50d' AND user_id='ef09d5af-818c-4310-8d52-7aec4bc9946d'"))
        role = r.scalar()
        print('Test2 Role:', role)

asyncio.run(main())
