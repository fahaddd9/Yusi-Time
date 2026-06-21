import uuid
import zoneinfo
from datetime import date, datetime, timedelta, timezone as dt_timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.time_entry import TimeEntry
from app.models.timesheet_submission import TimesheetSubmission
from app.models.submission_entry import SubmissionEntry
from app.models.workspace import Workspace
from app.models.user import User
from app.services import notification_service

async def _check_workflow_enabled(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    workspace = await db.get(Workspace, workspace_id)
    if not workspace or not workspace.approval_workflow_enabled:
        raise HTTPException(
            status_code=400, detail="Approval workflow is disabled", headers={"code": "BAD_REQUEST"}
        )
    return workspace

async def submit_week(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    week_start: date,
) -> TimesheetSubmission:
    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=400, detail="week_start must be a Monday", headers={"code": "INVALID_WEEK_START"}
        )

    workspace = await _check_workflow_enabled(db, workspace_id)

    # Check for existing pending submission
    stmt_check = select(TimesheetSubmission).where(
        TimesheetSubmission.workspace_id == workspace_id,
        TimesheetSubmission.user_id == user_id,
        TimesheetSubmission.week_start == week_start,
        TimesheetSubmission.status == "pending",
    )
    existing = await db.scalar(stmt_check)
    if existing:
        raise HTTPException(
            status_code=409, detail="Week is already submitted", headers={"code": "ALREADY_SUBMITTED"}
        )

    # Resolve date boundaries in workspace timezone
    tz_name = workspace.default_timezone or "UTC"
    if tz_name == "UTC":
        tz = dt_timezone.utc
    else:
        # Requires tzdata package on Windows
        tz = zoneinfo.ZoneInfo(tz_name)
        
    dt_start = datetime.combine(week_start, datetime.min.time(), tzinfo=tz)
    dt_end = dt_start + timedelta(days=7)
    
    start_utc = dt_start.astimezone(dt_timezone.utc)
    end_utc = dt_end.astimezone(dt_timezone.utc)

    stmt_entries = select(TimeEntry).where(
        TimeEntry.workspace_id == workspace_id,
        TimeEntry.user_id == user_id,
        TimeEntry.status == "draft",
        TimeEntry.start_time >= start_utc,
        TimeEntry.start_time < end_utc,
    )
    result = await db.execute(stmt_entries)
    draft_entries = result.scalars().all()

    if not draft_entries:
        raise HTTPException(
            status_code=400, detail="No entries to submit", headers={"code": "NO_ENTRIES_TO_SUBMIT"}
        )

    # Delete old submission_entries mappings to allow resubmission (avoids unique constraint)
    from sqlalchemy import delete
    entry_ids = [e.id for e in draft_entries]
    stmt_delete_old = delete(SubmissionEntry).where(SubmissionEntry.time_entry_id.in_(entry_ids))
    await db.execute(stmt_delete_old)

    # Create submission
    submission = TimesheetSubmission(
        workspace_id=workspace_id,
        user_id=user_id,
        week_start=week_start,
        status="pending",
    )
    db.add(submission)
    await db.flush()  # to get submission.id

    # Update entries to pending and create SubmissionEntry rows
    submission_entries = []
    for entry in draft_entries:
        entry.status = "pending"
        submission_entries.append(
            SubmissionEntry(
                submission_id=submission.id,
                time_entry_id=entry.id,
            )
        )
    
    db.add_all(submission_entries)

    # Notify managers/admins
    user = await db.get(User, user_id)
    user_name = user.full_name if user else "A user"
    
    await notification_service.create_for_role(
        db=db,
        workspace_id=workspace_id,
        roles=["admin", "manager"],
        event_type="timesheet_submitted",
        title="Timesheet Submitted",
        message=f"{user_name} submitted their timesheet for week of {week_start}.",
        metadata={"submission_id": str(submission.id), "week_start": str(week_start)},
    )

    return submission

async def approve_submission(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    submission_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> TimesheetSubmission:
    await _check_workflow_enabled(db, workspace_id)

    submission = await db.get(TimesheetSubmission, submission_id)
    if not submission or submission.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="Submission is not pending")

    submission.status = "approved"
    submission.reviewed_by_user_id = reviewer_id
    submission.reviewed_at = datetime.now(dt_timezone.utc)

    # Load entries and mark approved
    stmt_entries = select(TimeEntry).join(SubmissionEntry).where(
        SubmissionEntry.submission_id == submission_id
    )
    result = await db.execute(stmt_entries)
    entries = result.scalars().all()

    for entry in entries:
        entry.status = "approved"

    await notification_service.create(
        db=db,
        workspace_id=workspace_id,
        user_id=submission.user_id,
        event_type="timesheet_approved",
        title="Timesheet Approved",
        message=f"Your timesheet for week of {submission.week_start} has been approved.",
        metadata={"submission_id": str(submission.id)},
    )

    return submission

async def reject_submission(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    submission_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    note: str,
) -> TimesheetSubmission:
    if not note or not note.strip():
        raise HTTPException(status_code=422, detail="Rejection note is required")

    await _check_workflow_enabled(db, workspace_id)

    submission = await db.get(TimesheetSubmission, submission_id)
    if not submission or submission.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="Submission is not pending")

    submission.status = "rejected"
    submission.reviewed_by_user_id = reviewer_id
    submission.reviewed_at = datetime.now(dt_timezone.utc)
    submission.rejection_note = note.strip()

    # Load entries and mark draft
    stmt_entries = select(TimeEntry).join(SubmissionEntry).where(
        SubmissionEntry.submission_id == submission_id
    )
    result = await db.execute(stmt_entries)
    entries = result.scalars().all()

    for entry in entries:
        entry.status = "draft"

    await notification_service.create(
        db=db,
        workspace_id=workspace_id,
        user_id=submission.user_id,
        event_type="timesheet_rejected",
        title="Timesheet Rejected",
        message=f"Your timesheet for week of {submission.week_start} has been rejected.",
        metadata={"submission_id": str(submission.id), "note": submission.rejection_note},
    )

    return submission

async def list_pending_submissions(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None,
    limit: int,
    offset: int,
) -> tuple[list[TimesheetSubmission], int]:
    await _check_workflow_enabled(db, workspace_id)

    stmt = select(TimesheetSubmission).where(
        TimesheetSubmission.workspace_id == workspace_id,
        TimesheetSubmission.status == "pending"
    )
    if user_id:
        stmt = stmt.where(TimesheetSubmission.user_id == user_id)
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    stmt = stmt.order_by(TimesheetSubmission.submitted_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total

async def handle_workflow_disabled(db: AsyncSession, workspace_id: uuid.UUID) -> None:
    pass
