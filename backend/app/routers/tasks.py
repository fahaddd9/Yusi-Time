import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user, require_role, get_workspace_member
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskResponseViewer,
)
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=Dict[str, Any])
async def list_tasks(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """List tasks for a project."""
    tasks, total = await task_service.list_tasks(
        db, workspace_id, project_id, current_user.id, member.role, page, per_page
    )
    
    Schema = TaskResponseViewer if member.role == "viewer" else TaskResponse
    
    return {
        "data": [Schema.model_validate(t) for t in tasks],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_task(
    data: TaskCreate,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Create a task (Manager/Admin only)."""
    task = await task_service.create_task(db, workspace_id, data)
    return {"data": TaskResponse.model_validate(task)}


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: uuid.UUID,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """Get task details."""
    task = await task_service.get_task(db, workspace_id, project_id, task_id, current_user.id, member.role)
    
    Schema = TaskResponseViewer if member.role == "viewer" else TaskResponse
    return {"data": Schema.model_validate(task)}


@router.patch("/{task_id}", response_model=Dict[str, Any])
async def update_task(
    task_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: TaskUpdate,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update a task (Manager/Admin only)."""
    task = await task_service.update_task(db, workspace_id, task_id, data)
    return {"data": TaskResponse.model_validate(task)}


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def delete_task(
    task_id: uuid.UUID,
    workspace_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task (Manager/Admin only)."""
    await task_service.delete_task(db, workspace_id, task_id)
    return {"message": "Task deleted."}
