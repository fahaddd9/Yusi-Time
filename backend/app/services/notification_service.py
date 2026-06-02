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
