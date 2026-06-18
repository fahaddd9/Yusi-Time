import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.models.time_entry import TimeEntry
from sqlalchemy import select
from app.services import time_entry_service
from app.models.user import User
from app.models.workspace_member import WorkspaceMember

async def run():
    async with AsyncSessionLocal() as db:
        member = (await db.execute(select(WorkspaceMember))).scalars().first()
        entries, _ = await time_entry_service.list_entries(
            db=db,
            user_id=member.user_id,
            workspace_id=member.workspace_id,
            caller_role=member.role,
            cursor=None,
            limit=5,
            filter_user_id=None,
            project_id=None,
            status=None,
            billable=None,
            date_from="2026-06-15",
            date_to="2026-06-21",
            tag_ids_filter=None
        )
        print("API list_entries returned:", len(entries))
        if entries:
            e, user, project, task = entries[-1]  # Get an older one to ensure it has project
            d = time_entry_service._build_entry_dict(e, user, project, task)
            print(json.dumps(d, default=str, indent=2))

asyncio.run(run())
