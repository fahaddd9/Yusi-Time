"""
Notification service — Phase 2 minimal implementation.

Phase 2 only uses create_notification for workspace_deleted events.
Full notification system (bell, read/unread) is implemented in Phase 6.

This module is kept intentionally minimal — it provides the function
signature that workspace_service.soft_delete calls so Phase 2 works
end-to-end without coupling to the full notification system yet.
"""

import uuid as _uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification
from app.models.workspace_member import WorkspaceMember


async def create_notification(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    user_id: _uuid.UUID,
    event_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
) -> Notification:
    """
    Create a single notification for one user.

    Called by workspace_service.soft_delete_workspace and (in Phase 6) by
    the approval workflow.
    """
    notification = Notification(
        workspace_id=workspace_id,
        user_id=user_id,
        event_type=event_type,
        title=title,
        message=message,
        event_metadata=metadata,
    )
    db.add(notification)
    return notification


async def create_for_all_members(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    event_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
) -> list[Notification]:
    """
    Create notifications for every member of a workspace.

    Used by soft_delete_workspace to notify all members that the workspace
    has been scheduled for deletion. IMPLEMENTATION_PLAN §2.3.
    """
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    )
    members = result.scalars().all()

    notifications: list[Notification] = []
    for member in members:
        n = await create_notification(
            db=db,
            workspace_id=workspace_id,
            user_id=member.user_id,
            event_type=event_type,
            title=title,
            message=message,
            metadata=metadata,
        )
        notifications.append(n)
    return notifications

async def create(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    user_id: _uuid.UUID,
    event_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
) -> Notification:
    return await create_notification(db, workspace_id, user_id, event_type, title, message, metadata)

async def create_for_role(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    roles: list[str],
    event_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
) -> None:
    stmt = select(WorkspaceMember.user_id).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.role.in_(roles),
    )
    result = await db.execute(stmt)
    user_ids = result.scalars().all()
    
    notifications = [
        Notification(
            workspace_id=workspace_id,
            user_id=uid,
            event_type=event_type,
            title=title,
            message=message,
            event_metadata=metadata,
        )
        for uid in user_ids
    ]
    if notifications:
        db.add_all(notifications)

async def list_notifications(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    user_id: _uuid.UUID,
    unread_only: bool,
    limit: int,
    offset: int,
) -> tuple[list[Notification], int]:
    from sqlalchemy import func
    stmt = select(Notification).where(
        Notification.workspace_id == workspace_id,
        Notification.user_id == user_id,
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    
    # Get total unread across all pages
    unread_stmt = select(func.count()).select_from(Notification).where(
        Notification.workspace_id == workspace_id,
        Notification.user_id == user_id,
        Notification.read_at.is_(None)
    )
    unread_result = await db.execute(unread_stmt)
    unread_count = unread_result.scalar_one()

    return items, total, unread_count

async def mark_read(
    db: AsyncSession,
    user_id: _uuid.UUID,
    notification_ids: list[_uuid.UUID],
) -> None:
    from sqlalchemy import update
    from datetime import datetime, UTC
    if not notification_ids:
        return
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids),
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(UTC))
    )
    await db.execute(stmt)

async def mark_all_read(
    db: AsyncSession,
    workspace_id: _uuid.UUID,
    user_id: _uuid.UUID,
) -> None:
    from sqlalchemy import update
    from datetime import datetime, UTC
    stmt = (
        update(Notification)
        .where(
            Notification.workspace_id == workspace_id,
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(UTC))
    )
    await db.execute(stmt)
