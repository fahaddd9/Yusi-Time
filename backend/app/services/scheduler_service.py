"""
Scheduler Service — Phase 6.5, Addendum §5.2.

Sets up an in-process APScheduler (AsyncIOScheduler) with two recurring jobs:

  Job 1 — check_workspace_attendance (every 1 minute)
    Iterates all workspaces with attendance_enabled=True.
    For each: calls attendance_service.check_work_start_for_workspace()
    which evaluates F1 trigger conditions per Member and creates
    attendance_notification records. Then fires push notifications for
    triggered Members via push_service (imported lazily to avoid circular).

  Job 2 — check_daily_shortfall (every 1 minute)
    When a workspace's midnight passes (checked via workspace timezone),
    calls attendance_service.check_daily_shortfall_for_workspace()
    to record daily_hours_shortfall notifications for Admins/Managers.

Architecture decisions (Addendum §5.2, TRD §5 — single-instance ECS Fargate):
  - In-process scheduler; no Redis/Celery needed for MVP scale.
  - RULE B-06: Jobs open their own DB sessions via async_sessionmaker
    (NOT the per-request session — background jobs are not request-scoped).
  - Scheduler runs in the same event loop as FastAPI (AsyncIOScheduler
    with asyncio executor for async job functions).
  - Two separate 1-minute jobs rather than one combined — cleaner separation,
    easier to disable individually if needed.
  - Error isolation: per-workspace try/except so one bad workspace doesn't
    prevent others from being processed.

Startup/shutdown wiring is in main.py lifespan context manager.
"""

from __future__ import annotations

import logging
import zoneinfo
from datetime import datetime, timedelta, timezone as dt_timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.services import attendance_service

logger = logging.getLogger(__name__)

# Module-level scheduler instance (singleton)
# Accessed from main.py lifespan to start/stop cleanly
scheduler: AsyncIOScheduler | None = None


# ── Internal helpers ────────────────────────────────────────────────────────────

async def _get_attendance_enabled_workspaces(db: AsyncSession) -> list[Workspace]:
    """
    Fetch all non-deleted workspaces with attendance_enabled=True.
    Addendum §5.2: scheduler only operates on enabled workspaces.
    """
    stmt = select(Workspace).where(
        Workspace.attendance_enabled.is_(True),
        Workspace.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_workspace_members(
    db: AsyncSession, workspace_id
) -> list[WorkspaceMember]:
    """Fetch all members for a workspace (all roles — service filters by role)."""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _midnight_just_passed(workspace: Workspace) -> tuple[bool, object]:
    """
    Check if midnight JUST passed in the workspace timezone (within the last minute).
    Addendum §5.2: F2 shortfall check fires at midnight in workspace timezone.

    Returns (True, yesterday_date) if midnight just passed, (False, None) otherwise.
    The scheduler calls this every minute — we check if the current minute is
    the first minute of a new day (i.e., HH:MM == 00:00).
    """
    tz_name = workspace.default_timezone or "UTC"
    try:
        tz = zoneinfo.ZoneInfo(tz_name) if tz_name != "UTC" else dt_timezone.utc
    except Exception:
        tz = dt_timezone.utc

    now = datetime.now(tz=tz)

    # Midnight just passed: current hour=0, minute=0 (first minute of new day)
    if now.hour == 0 and now.minute == 0:
        yesterday = now.date() - timedelta(days=1)
        return True, yesterday
    return False, None


# ── Job 1: F1 — Work Start Check (every 1 minute) ──────────────────────────────

async def check_workspace_attendance() -> None:
    """
    F1 scheduler job — fires every 1 minute.
    Addendum §5.2 (in-process APScheduler, RULE B-06 separate DB session).

    For each attendance-enabled workspace, evaluates F1 trigger conditions
    per Member and creates attendance_notification records for Members who
    need to be prompted. Then dispatches push notifications (Step 6.5.6).
    """
    logger.debug("Scheduler: running F1 work-start check")
    try:
        async with AsyncSessionLocal() as db:
            workspaces = await _get_attendance_enabled_workspaces(db)
            if not workspaces:
                return

            for workspace in workspaces:
                try:
                    members = await _get_workspace_members(db, workspace.id)
                    triggered_user_ids = await attendance_service.check_work_start_for_workspace(
                        db=db,
                        workspace=workspace,
                        members=members,
                    )

                    if triggered_user_ids:
                        await db.flush()
                        logger.info(
                            "F1 triggered for %d member(s) in workspace %s",
                            len(triggered_user_ids),
                            workspace.id,
                        )
                        # Fire push notifications — lazy import avoids circular
                        # at module level; push_service is imported only when needed
                        try:
                            from app.services import push_service  # Step 6.5.6
                            for user_id in triggered_user_ids:
                                await push_service.send_work_start_push(
                                    db=db,
                                    workspace=workspace,
                                    user_id=user_id,
                                )
                        except ImportError:
                            # push_service not yet available (Step 6.5.5 runs before 6.5.6)
                            pass

                except Exception as exc:
                    # Per-workspace error isolation (Addendum §5.2)
                    logger.exception(
                        "F1 check failed for workspace %s: %s",
                        workspace.id,
                        exc,
                    )

            await db.commit()

    except Exception as exc:
        logger.exception("F1 scheduler job crashed: %s", exc)


# ── Job 2: F2 — Daily Shortfall Check (every 1 minute) ─────────────────────────

async def check_daily_shortfall() -> None:
    """
    F2 scheduler job — fires every 1 minute, detects when midnight passes.
    Addendum §5.2, §2.3.

    At midnight in each workspace's timezone (i.e., when now.hour==0, now.minute==0),
    evaluates whether each Member met their daily_required_hours target yesterday.
    Creates daily_hours_shortfall notifications for each Admin/Manager per Member
    who fell short.
    """
    logger.debug("Scheduler: running F2 daily-shortfall check")
    try:
        async with AsyncSessionLocal() as db:
            workspaces = await _get_attendance_enabled_workspaces(db)
            if not workspaces:
                return

            for workspace in workspaces:
                try:
                    midnight_passed, yesterday = _midnight_just_passed(workspace)
                    if not midnight_passed:
                        continue  # Not midnight for this workspace yet

                    members = await _get_workspace_members(db, workspace.id)
                    created = await attendance_service.check_daily_shortfall_for_workspace(
                        db=db,
                        workspace=workspace,
                        members=members,
                        check_date=yesterday,  # type: ignore[arg-type]
                    )

                    if created:
                        await db.flush()
                        logger.info(
                            "F2 shortfall: %d notification(s) created for workspace %s on %s",
                            len(created),
                            workspace.id,
                            yesterday,
                        )

                except Exception as exc:
                    # Per-workspace error isolation
                    logger.exception(
                        "F2 shortfall check failed for workspace %s: %s",
                        workspace.id,
                        exc,
                    )

            await db.commit()

    except Exception as exc:
        logger.exception("F2 scheduler job crashed: %s", exc)


# ── Lifecycle: start / shutdown ─────────────────────────────────────────────────

def create_scheduler() -> AsyncIOScheduler:
    """
    Build and configure the AsyncIOScheduler.
    Called from main.py lifespan before app starts accepting requests.

    Both jobs use interval trigger, every 60 seconds.
    max_instances=1 prevents overlapping runs if a job takes > 1 minute
    (Addendum §5.2: scheduler must not queue overlapping runs).
    """
    s = AsyncIOScheduler()

    # F1 — Work Start Prompt (every 1 minute)
    s.add_job(
        check_workspace_attendance,
        trigger="interval",
        seconds=60,
        id="f1_work_start_check",
        name="F1 Work Start Check",
        max_instances=1,
        replace_existing=True,
        coalesce=True,  # Merge missed executions into a single catch-up run
    )

    # F2 — Daily Shortfall (every 1 minute, acts only at midnight)
    s.add_job(
        check_daily_shortfall,
        trigger="interval",
        seconds=60,
        id="f2_daily_shortfall",
        name="F2 Daily Shortfall Check",
        max_instances=1,
        replace_existing=True,
        coalesce=True,
    )

    return s


def start_scheduler() -> AsyncIOScheduler:
    """
    Create and start the scheduler.
    Called from main.py lifespan on startup.
    """
    global scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("APScheduler started: F1 and F2 attendance jobs running every 60s")
    return scheduler


def stop_scheduler() -> None:
    """
    Gracefully stop the scheduler.
    Called from main.py lifespan on shutdown.
    """
    global scheduler
    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
        scheduler = None
