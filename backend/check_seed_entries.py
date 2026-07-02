import asyncio
import datetime
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.workspace import Workspace
from app.models.time_entry import TimeEntry

async def main():
    async with AsyncSessionLocal() as session:
        ws_query = await session.execute(select(Workspace).where(Workspace.name == "Yusi Time"))
        workspace = ws_query.scalar_one_or_none()
        
        test3_query = await session.execute(select(User).where(User.email == "test3@gmail.com"))
        test3 = test3_query.scalar_one_or_none()
        
        bob_query = await session.execute(select(User).where(User.email == "bob@email.com"))
        bob = bob_query.scalar_one_or_none()
        
        entries_query = await session.execute(
            select(TimeEntry).where(
                TimeEntry.workspace_id == workspace.id,
                TimeEntry.user_id.in_([test3.id, bob.id])
            )
        )
        entries = entries_query.scalars().all()
        
        print(f"Total entries found: {len(entries)}")
        
        # group by user
        for u in [test3, bob]:
            u_entries = [e for e in entries if e.user_id == u.id]
            print(f"\nUser: {u.email} ({len(u_entries)} entries)")
            
            # Print entries sorted by start_time
            for e in sorted(u_entries, key=lambda x: x.start_time):
                print(f" - {e.start_time.date()} | {e.status} | Billable: {e.billable} | Proj: {e.project_id}")

if __name__ == "__main__":
    asyncio.run(main())
