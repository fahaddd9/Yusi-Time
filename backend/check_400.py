import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        users = await db.execute(select(User).where(User.full_name == "Bob"))
        user = users.scalars().first()
        
        entry = (await db.execute(select(TimeEntry).where(TimeEntry.user_id == user.id))).scalars().first()
        workspace_id = entry.workspace_id
        
        from app.services import time_entry_service
        enriched, next_cursor = await time_entry_service.list_entries(
            db=db,
            user_id=user.id,
            workspace_id=workspace_id,
            caller_role="member",
            cursor=None,
            limit=200,
            filter_user_id=user.id,
            project_id=None,
            status=None,
            billable=None,
            date_from="2026-06-15",
            date_to="2026-06-21",
            tag_ids_filter=[],
        )
        print(f"List Entries for Bob Jun 15 week: {len(enriched)}")
        for e in enriched:
            print(f" - {e[0].id} at {e[0].start_time}")

if __name__ == "__main__":
    asyncio.run(main())
