import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user, require_role, get_workspace_member
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectResponseViewer,
    ProjectListItem,
    ProjectListItemViewer,
    ProjectMemberCreate,
    ProjectMemberResponse,
)
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=Dict[str, Any])
async def list_projects(
    workspace_id: uuid.UUID,
    status: str = "active",
    client_id: Optional[uuid.UUID] = None,
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """List visible projects."""
    projects, total = await project_service.list_projects(
        db, workspace_id, current_user.id, member.role, status, client_id, page, per_page
    )
    
    Schema = ProjectListItemViewer if member.role == "viewer" else ProjectListItem
    
    return {
        "data": [Schema.model_validate(p) for p in projects],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_project(
    workspace_id: uuid.UUID,
    data: ProjectCreate,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Create a project (Manager/Admin only)."""
    project = await project_service.create_project(db, workspace_id, data)
    return {"data": ProjectResponse.model_validate(project)}


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    project_dict = await project_service.get_project(db, workspace_id, project_id, current_user.id, member.role)
    
    Schema = ProjectResponseViewer if member.role == "viewer" else ProjectResponse
    return {"data": Schema.model_validate(project_dict)}


@router.patch("/{project_id}", response_model=Dict[str, Any])
async def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update a project (Manager/Admin only)."""
    project = await project_service.update_project(db, workspace_id, project_id, data)
    return {"data": ProjectResponse.model_validate(project)}


@router.post("/{project_id}/archive", response_model=Dict[str, Any])
async def archive_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Archive a project (Manager/Admin only)."""
    project = await project_service.archive_project(db, workspace_id, project_id)
    return {"data": ProjectResponse.model_validate(project)}


@router.delete("/{project_id}", response_model=Dict[str, Any])
async def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project (Admin only)."""
    await project_service.delete_project(db, workspace_id, project_id)
    return {"message": "Project deleted."}


@router.get("/{project_id}/members", response_model=Dict[str, Any])
async def list_project_members(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """List explicitly assigned members (Manager/Admin only)."""
    members = await project_service.list_project_members(db, workspace_id, project_id)
    return {"data": [ProjectMemberResponse.model_validate(m) for m in members]}


@router.post("/{project_id}/members", response_model=Dict[str, Any], status_code=201)
async def add_project_member(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Assign member to private project (Manager/Admin only)."""
    pm = await project_service.add_project_member(db, workspace_id, project_id, data.user_id, current_user.id)
    return {"data": ProjectMemberResponse.model_validate(pm)}


@router.delete("/{project_id}/members/{user_id}", response_model=Dict[str, Any])
async def remove_project_member(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Remove member from project (Manager/Admin only)."""
    await project_service.remove_project_member(db, workspace_id, project_id, user_id)
    return {"message": "Member removed from project."}
