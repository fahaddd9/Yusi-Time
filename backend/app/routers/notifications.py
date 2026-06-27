import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, require_role, get_current_user
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.notification import NotificationReadRequest
from app.services import notification_service, attendance_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
async def list_notifications(
    workspace_id: uuid.UUID,
    unread_only: bool = Query(False),
    page: int = 1,
    per_page: int = 20,
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member", "viewer")),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    notifications, total, unread_count = await notification_service.list_notifications(
        db=db,
        workspace_id=workspace_id,
        user_id=member.user_id,
        unread_only=unread_only,
        limit=per_page,
        offset=offset,
    )
    return {
        "data": notifications,
        "total": total,
        "unread_count": unread_count,
        "page": (offset // per_page) + 1,
        "per_page": per_page,
    }

@router.post("/read")
async def mark_read(
    request: NotificationReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await notification_service.mark_read(
        db=db,
        user_id=current_user.id,
        notification_ids=request.ids,
    )
    await attendance_service.mark_read(
        db=db,
        user_id=current_user.id,
        notification_ids=request.ids,
    )
    await db.commit()
    return {"message": "Notifications marked as read."}

@router.post("/read-all")
async def mark_all_read(
    workspace_id: uuid.UUID,
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member", "viewer")),
    db: AsyncSession = Depends(get_db),
):
    await notification_service.mark_all_read(
        db=db,
        workspace_id=workspace_id,
        user_id=member.user_id,
    )
    await attendance_service.mark_all_read(
        db=db,
        workspace_id=workspace_id,
        user_id=member.user_id,
    )
    await db.commit()
    return {"message": "All notifications marked as read."}
