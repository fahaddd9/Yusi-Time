import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://yusitime:yusitime_dev@localhost:5432/yusitime")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TYPE workspace_role AS ENUM ('admin', 'manager', 'member', 'viewer');"))
        print("Type created successfully.")

asyncio.run(main())
