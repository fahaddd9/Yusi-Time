import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.services import time_entry_service
from app.models.workspace_member import WorkspaceMember
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        member = (await db.execute(select(WorkspaceMember))).scalars().first()
        entries, _ = await time_entry_service.list_entries(
            db=db,
            user_id=member.user_id,
            workspace_id=member.workspace_id,
            caller_role=member.role,
            cursor=None,
            limit=500,
            filter_user_id=None,
            project_id=None,
            status=None,
            billable=None,
            date_from="2026-06-15",
            date_to="2026-06-21",
            tag_ids_filter=None
        )
        
        # Simulate frontend transformEntries
        print(f"Total API entries: {len(entries)}")
        
        day_keys = ["2026-06-15", "2026-06-16", "2026-06-17", "2026-06-18", "2026-06-19", "2026-06-20", "2026-06-21"]
        grouped = {}
        
        for e_tuple in entries:
            e = e_tuple[0]
            if not e.start_time or not e.duration_seconds:
                continue
                
            # Simulate frontend new Date(e.start_time)
            # e.start_time is a timezone-aware datetime in UTC
            # But the frontend parses the ISO string
            start_time_str = e.start_time.isoformat()
            if start_time_str.endswith("+00:00"):
                start_time_str = start_time_str[:-6] + "Z"
            
            # Since frontend runs in GMT+0500, let's adjust by +5 hours
            from datetime import timedelta
            local_dt = e.start_time + timedelta(hours=5)
            day = local_dt.strftime("%Y-%m-%d")
            
            if day not in day_keys:
                print(f"Skipping day {day} for entry {e.id}")
                continue
                
            pkey = str(e.project_id)
            tkey = str(e.task_id) if e.task_id else "__no_task__"
            
            if pkey not in grouped: grouped[pkey] = {}
            if tkey not in grouped[pkey]: grouped[pkey][tkey] = 0
            grouped[pkey][tkey] += 1
            
        print("Grouped results (project_id -> task_id -> count):")
        print(json.dumps(grouped, indent=2))

asyncio.run(run())
