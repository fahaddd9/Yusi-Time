import asyncio
import datetime
import random
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry

async def main():
    async with AsyncSessionLocal() as session:
        # Find users
        test3_query = await session.execute(select(User).where(User.email == "test3@gmail.com"))
        test3 = test3_query.scalar_one_or_none()
        
        bob_query = await session.execute(select(User).where(User.email == "bob@email.com"))
        bob = bob_query.scalar_one_or_none()
        
        if not test3 or not bob:
            print(f"Users not found! test3: {bool(test3)}, bob: {bool(bob)}")
            return
            
        print(f"Found users - test3: {test3.id}, bob: {bob.id}")
        
        # Find Yusi Time workspace
        ws_query = await session.execute(select(Workspace).where(Workspace.name == "Yusi Time"))
        workspace = ws_query.scalar_one_or_none()
        if not workspace:
            print("Workspace 'Yusi Time' not found")
            return
            
        workspace_id = workspace.id
        print(f"Using workspace: {workspace.name} ({workspace_id})")
        
        # Ensure they are members
        for u in [test3, bob]:
            member_check = await session.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == u.id
                )
            )
            if not member_check.scalar_one_or_none():
                print(f"Adding user {u.email} to workspace Yusi Time")
                wm = WorkspaceMember(workspace_id=workspace_id, user_id=u.id, role="member")
                session.add(wm)
        await session.commit()
        
        # Get or create projects
        proj_query = await session.execute(select(Project).where(Project.workspace_id == workspace_id))
        projects = proj_query.scalars().all()
        
        if len(projects) < 2:
            print("Creating missing projects...")
            p1 = Project(workspace_id=workspace_id, name="Test Project 1")
            p2 = Project(workspace_id=workspace_id, name="Test Project 2")
            session.add_all([p1, p2])
            await session.commit()
            await session.refresh(p1)
            await session.refresh(p2)
        else:
            p1, p2 = projects[0], projects[1]
            
        print(f"Using projects: {p1.name} ({p1.id}), {p2.name} ({p2.id})")
        
        # Get or create tasks for projects
        async def get_or_create_task(proj):
            t_q = await session.execute(select(Task).where(Task.project_id == proj.id))
            tasks = t_q.scalars().all()
            if tasks:
                return tasks[0]
            print(f"Creating task for project {proj.name}...")
            task = Task(workspace_id=workspace_id, project_id=proj.id, name=f"Task for {proj.name}")
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task
            
        t1 = await get_or_create_task(p1)
        t2 = await get_or_create_task(p2)
        
        # Clean existing entries for these users in ALL workspaces to fix previous mistake
        await session.execute(
            TimeEntry.__table__.delete().where(
                TimeEntry.user_id.in_([test3.id, bob.id])
            )
        )
        await session.commit()
        print("Cleaned old entries.")

        # Dates
        now = datetime.datetime.now(datetime.UTC)
        # week A (3 weeks ago)
        week_a = now - datetime.timedelta(days=21)
        # week B (2 weeks ago)
        week_b = now - datetime.timedelta(days=14)
        # week C (this week)
        week_c = now - datetime.timedelta(days=2)
        
        entries = []
        
        def make_entry(user_id, date, proj, task, billable, status, hours=2):
            return TimeEntry(
                workspace_id=workspace_id,
                user_id=user_id,
                project_id=proj.id if proj else None,
                task_id=task.id if task else None,
                start_time=date,
                end_time=date + datetime.timedelta(hours=hours),
                duration_seconds=hours * 3600,
                description=f"Test entry for {status}",
                billable=billable,
                status=status,
                hourly_rate_cents=10000 if billable else None,
                billable_amount_cents=10000 * hours if billable else None
            )

        # test3@gmail.com
        # - Week A: 3 entries, 2 billable, 1 non-billable, across 2 projects
        entries.append(make_entry(test3.id, week_a, p1, t1, True, "draft"))
        entries.append(make_entry(test3.id, week_a + datetime.timedelta(hours=3), p2, t2, True, "pending"))
        entries.append(make_entry(test3.id, week_a + datetime.timedelta(hours=6), p1, t1, False, "approved"))
        
        # - Week B: 4 entries, all billable, 1 project
        entries.append(make_entry(test3.id, week_b, p1, t1, True, "approved"))
        entries.append(make_entry(test3.id, week_b + datetime.timedelta(hours=3), p1, t1, True, "approved"))
        entries.append(make_entry(test3.id, week_b + datetime.timedelta(hours=6), p1, t1, True, "draft"))
        entries.append(make_entry(test3.id, week_b + datetime.timedelta(hours=9), p1, t1, True, "pending"))
        
        # - Week C: 2 entries, 1 billable, 1 non-billable, 2 different projects
        entries.append(make_entry(test3.id, week_c, p1, t1, True, "draft"))
        entries.append(make_entry(test3.id, week_c + datetime.timedelta(hours=3), p2, t2, False, "pending"))
        
        # bob@email.com
        # - Week B: 2 entries, both billable
        entries.append(make_entry(bob.id, week_b, p1, t1, True, "approved"))
        entries.append(make_entry(bob.id, week_b + datetime.timedelta(hours=3), p2, t2, True, "draft"))
        
        # - Week C: 1 entry, billable
        entries.append(make_entry(bob.id, week_c, p1, t1, True, "pending"))
        
        session.add_all(entries)
        await session.commit()
        print(f"Created {len(entries)} time entries successfully.")

if __name__ == "__main__":
    asyncio.run(main())
