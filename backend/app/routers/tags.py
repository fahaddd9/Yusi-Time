import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_workspace_member, require_role
from app.models.workspace_member import WorkspaceMember
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
)
from app.services import tag_service

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=Dict[str, Any])
async def list_tags(
    workspace_id: uuid.UUID,
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """List all tags in a workspace."""
    tags = await tag_service.list_tags(db, workspace_id)
    
    return {
        "data": [TagResponse.model_validate(t) for t in tags],
    }


@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_tag(
    data: TagCreate,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Create a tag (Manager/Admin only)."""
    tag = await tag_service.create_tag(db, workspace_id, data)
    return {"data": TagResponse.model_validate(tag)}


@router.patch("/{tag_id}", response_model=Dict[str, Any])
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update a tag (Manager/Admin only)."""
    tag = await tag_service.update_tag(db, workspace_id, tag_id, data)
    return {"data": TagResponse.model_validate(tag)}


@router.delete("/{tag_id}", response_model=Dict[str, Any])
async def delete_tag(
    tag_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag (Admin only)."""
    await tag_service.delete_tag(db, workspace_id, tag_id)
    return {"message": "Tag deleted."}
