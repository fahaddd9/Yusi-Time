import uuid
from typing import Tuple, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.client import Client
from app.models.project import Project
from app.schemas.client import ClientCreate, ClientUpdate


async def list_clients(
    db: AsyncSession, workspace_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> Tuple[Sequence[dict], int]:
    """List clients with pagination and project count."""
    # Count total clients
    count_stmt = select(func.count()).select_from(Client).where(Client.workspace_id == workspace_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    if total == 0:
        return [], 0

    # Fetch paginated clients with project count
    stmt = (
        select(Client, func.count(Project.id).label("project_count"))
        .outerjoin(Project, Project.client_id == Client.id)
        .where(Client.workspace_id == workspace_id)
        .group_by(Client.id)
        .order_by(Client.name.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Format result to match schema
    clients = []
    for client, project_count in rows:
        client_dict = client.__dict__.copy()
        client_dict["project_count"] = project_count
        clients.append(client_dict)

    return clients, total


async def get_client(db: AsyncSession, workspace_id: uuid.UUID, client_id: uuid.UUID) -> Client:
    """Get a single client by ID."""
    stmt = select(Client).where(Client.id == client_id, Client.workspace_id == workspace_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail={"detail": "Client not found", "code": "NOT_FOUND"})
    return client


async def create_client(db: AsyncSession, workspace_id: uuid.UUID, data: ClientCreate) -> Client:
    """Create a new client."""
    # Check uniqueness
    stmt = select(Client).where(Client.workspace_id == workspace_id, Client.name == data.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={"detail": "Client name already exists in this workspace.", "code": "DUPLICATE_NAME"},
        )

    client = Client(
        workspace_id=workspace_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        hourly_rate_cents=data.hourly_rate_cents,
    )
    db.add(client)
    await db.flush()
    return client


async def update_client(
    db: AsyncSession, workspace_id: uuid.UUID, client_id: uuid.UUID, data: ClientUpdate
) -> Client:
    """Update an existing client."""
    client = await get_client(db, workspace_id, client_id)

    # Check uniqueness if name is changed
    if data.name is not None and data.name != client.name:
        stmt = select(Client).where(Client.workspace_id == workspace_id, Client.name == data.name)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={"detail": "Client name already exists in this workspace.", "code": "DUPLICATE_NAME"},
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)

    await db.flush()
    return client


async def delete_client(db: AsyncSession, workspace_id: uuid.UUID, client_id: uuid.UUID) -> None:
    """Delete a client (Admin only enforced by router)."""
    client = await get_client(db, workspace_id, client_id)
    await db.delete(client)
    await db.flush()
