import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


async def list_tags(db: AsyncSession, workspace_id: uuid.UUID) -> Sequence[Tag]:
    """List all tags for a workspace."""
    stmt = select(Tag).where(Tag.workspace_id == workspace_id).order_by(Tag.name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_tag(db: AsyncSession, workspace_id: uuid.UUID, tag_id: uuid.UUID) -> Tag:
    """Get a specific tag."""
    stmt = select(Tag).where(Tag.id == tag_id, Tag.workspace_id == workspace_id)
    tag = (await db.execute(stmt)).scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail={"detail": "Tag not found", "code": "NOT_FOUND"})
    return tag


async def create_tag(db: AsyncSession, workspace_id: uuid.UUID, data: TagCreate) -> Tag:
    """Create a tag, ensuring name is unique in workspace."""
    stmt = select(Tag).where(Tag.workspace_id == workspace_id, Tag.name == data.name)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"detail": "Duplicate tag name", "code": "DUPLICATE_NAME"})

    tag = Tag(workspace_id=workspace_id, **data.model_dump())
    db.add(tag)
    await db.flush()
    return tag


async def update_tag(db: AsyncSession, workspace_id: uuid.UUID, tag_id: uuid.UUID, data: TagUpdate) -> Tag:
    """Update a tag."""
    tag = await get_tag(db, workspace_id, tag_id)

    if data.name is not None and data.name != tag.name:
        check = select(Tag).where(Tag.workspace_id == workspace_id, Tag.name == data.name)
        if (await db.execute(check)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail={"detail": "Duplicate tag name", "code": "DUPLICATE_NAME"})

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(tag, k, v)
        
    await db.flush()
    return tag


async def delete_tag(db: AsyncSession, workspace_id: uuid.UUID, tag_id: uuid.UUID) -> None:
    """Delete a tag."""
    tag = await get_tag(db, workspace_id, tag_id)
    await db.delete(tag)
    await db.flush()
