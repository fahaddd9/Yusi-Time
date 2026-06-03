import uuid
from typing import Tuple, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException

from app.models.task import Task
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.workspace_member import WorkspaceMember
from app.schemas.task import TaskCreate, TaskUpdate


async def list_tasks(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    caller_id: uuid.UUID,
    caller_role: str,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[Sequence[Task], int]:
    """List tasks for a project, verifying visibility."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    if caller_role in ["member", "viewer"]:
        project_stmt = project_stmt.outerjoin(ProjectMember, (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == caller_id))
        project_stmt = project_stmt.where(or_(Project.visibility == "public", ProjectMember.user_id.is_not(None)))
    
    if not (await db.execute(project_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"detail": "Project not found or access denied", "code": "NOT_FOUND"})

    count_stmt = select(func.count()).select_from(Task).where(Task.project_id == project_id)
    total = (await db.execute(count_stmt)).scalar() or 0
    if total == 0:
        return [], 0

    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.name.asc()).offset((page - 1) * per_page).limit(per_page)
    tasks = (await db.execute(stmt)).scalars().all()
    return tasks, total


async def get_task(
    db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, caller_id: uuid.UUID, caller_role: str
) -> Task:
    """Get a task, verifying project visibility."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    if caller_role in ["member", "viewer"]:
        project_stmt = project_stmt.outerjoin(ProjectMember, (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == caller_id))
        project_stmt = project_stmt.where(or_(Project.visibility == "public", ProjectMember.user_id.is_not(None)))
    
    if not (await db.execute(project_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"detail": "Project not found or access denied", "code": "NOT_FOUND"})

    task_stmt = select(Task).where(Task.id == task_id, Task.project_id == project_id)
    task = (await db.execute(task_stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"detail": "Task not found", "code": "NOT_FOUND"})
    return task


async def create_task(db: AsyncSession, workspace_id: uuid.UUID, data: TaskCreate) -> Task:
    """Create a new task."""
    project_stmt = select(Project).where(Project.id == data.project_id, Project.workspace_id == workspace_id)
    if not (await db.execute(project_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"detail": "Project not found in workspace", "code": "BAD_REQUEST"})

    check_name = select(Task).where(Task.project_id == data.project_id, Task.name == data.name)
    if (await db.execute(check_name)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"detail": "Duplicate task name in project", "code": "DUPLICATE_NAME"})

    if data.assignee_user_id:
        check_member = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == data.assignee_user_id)
        if not (await db.execute(check_member)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail={"detail": "Assignee is not a workspace member", "code": "BAD_REQUEST"})

    task = Task(workspace_id=workspace_id, **data.model_dump(exclude_unset=True))
    db.add(task)
    await db.flush()
    return task


async def update_task(db: AsyncSession, workspace_id: uuid.UUID, task_id: uuid.UUID, data: TaskUpdate) -> Task:
    """Update a task."""
    task_stmt = select(Task).where(Task.id == task_id, Task.workspace_id == workspace_id)
    task = (await db.execute(task_stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"detail": "Task not found", "code": "NOT_FOUND"})

    if data.name is not None and data.name != task.name:
        check_name = select(Task).where(Task.project_id == task.project_id, Task.name == data.name)
        if (await db.execute(check_name)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail={"detail": "Duplicate task name in project", "code": "DUPLICATE_NAME"})

    if data.assignee_user_id is not None:
        check_member = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == data.assignee_user_id)
        if not (await db.execute(check_member)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail={"detail": "Assignee is not a workspace member", "code": "BAD_REQUEST"})

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
        
    await db.flush()
    return task


async def delete_task(db: AsyncSession, workspace_id: uuid.UUID, task_id: uuid.UUID) -> None:
    """Delete a task. Cascades to NULL on time_entries."""
    task_stmt = select(Task).where(Task.id == task_id, Task.workspace_id == workspace_id)
    task = (await db.execute(task_stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"detail": "Task not found", "code": "NOT_FOUND"})

    await db.delete(task)
    await db.flush()
