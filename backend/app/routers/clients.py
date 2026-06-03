import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_workspace_member, require_role
from app.models.workspace_member import WorkspaceMember
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientResponseViewer,
    ClientListItem,
    ClientListItemViewer,
)
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=Dict[str, Any])
async def list_clients(
    workspace_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """List clients in a workspace."""
    clients, total = await client_service.list_clients(db, workspace_id, page, per_page)
    
    # Select response schema based on role
    Schema = ClientListItemViewer if member.role == "viewer" else ClientListItem
    
    return {
        "data": [Schema.model_validate(c) for c in clients],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_client(
    workspace_id: uuid.UUID,
    data: ClientCreate,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client (Admin/Manager only)."""
    client = await client_service.create_client(db, workspace_id, data)
    return {"data": ClientResponse.model_validate(client)}


@router.get("/{client_id}", response_model=Dict[str, Any])
async def get_client(
    workspace_id: uuid.UUID,
    client_id: uuid.UUID,
    member: WorkspaceMember = Depends(get_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """Get a single client by ID."""
    client = await client_service.get_client(db, workspace_id, client_id)
    
    Schema = ClientResponseViewer if member.role == "viewer" else ClientResponse
    return {"data": Schema.model_validate(client)}


@router.patch("/{client_id}", response_model=Dict[str, Any])
async def update_client(
    workspace_id: uuid.UUID,
    client_id: uuid.UUID,
    data: ClientUpdate,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update a client (Admin/Manager only)."""
    client = await client_service.update_client(db, workspace_id, client_id, data)
    return {"data": ClientResponse.model_validate(client)}


@router.delete("/{client_id}", response_model=Dict[str, Any])
async def delete_client(
    workspace_id: uuid.UUID,
    client_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a client (Admin only)."""
    await client_service.delete_client(db, workspace_id, client_id)
    return {"message": "Client deleted. Linked projects unassigned."}
