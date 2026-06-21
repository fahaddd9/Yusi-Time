import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role, get_current_user
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.schemas.approval import SubmitWeekRequest, RejectSubmissionRequest, TimesheetSubmissionResponse
from app.services import approval_service

router = APIRouter(prefix="/approvals", tags=["Approvals"])

@router.post("/submit", response_model=dict, status_code=201)
async def submit_week(
    workspace_id: uuid.UUID,
    data: SubmitWeekRequest,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("admin", "manager", "member")),
    db: AsyncSession = Depends(get_db),
):
    submission = await approval_service.submit_week(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        week_start=data.week_start,
    )
    return {"data": TimesheetSubmissionResponse.model_validate(submission)}

@router.get("/pending", response_model=dict)
async def list_pending(
    workspace_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    page: int = 1,
    per_page: int = 20,
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    submissions, total = await approval_service.list_pending_submissions(
        db=db,
        workspace_id=workspace_id,
        user_id=user_id,
        limit=per_page,
        offset=offset,
    )
    return {
        "data": [TimesheetSubmissionResponse.model_validate(s) for s in submissions],
        "total": total,
        "page": page,
        "per_page": per_page,
    }

@router.post("/{submission_id}/approve", response_model=dict)
async def approve_submission(
    workspace_id: uuid.UUID,
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    submission = await approval_service.approve_submission(
        db=db,
        workspace_id=workspace_id,
        submission_id=submission_id,
        reviewer_id=current_user.id,
    )
    return {"data": TimesheetSubmissionResponse.model_validate(submission)}

@router.post("/{submission_id}/reject", response_model=dict)
async def reject_submission(
    workspace_id: uuid.UUID,
    submission_id: uuid.UUID,
    data: RejectSubmissionRequest,
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    submission = await approval_service.reject_submission(
        db=db,
        workspace_id=workspace_id,
        submission_id=submission_id,
        reviewer_id=current_user.id,
        note=data.note,
    )
    return {"data": TimesheetSubmissionResponse.model_validate(submission)}
