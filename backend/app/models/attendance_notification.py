"""
AttendanceNotification model — maps to `attendance_notifications` table.

Addendum §3.2 — dedicated table for attendance-specific notifications,
separate from the general `notifications` table because:
  - `daily_hours_shortfall` requires recipient_user_id != subject user_id
    (role-broadcast: each Admin/Manager gets their own row)
  - Needs additional typed fields: related_date, late_by_minutes, hours_logged
  - Uses a separate `notification_type` with attendance-specific values
    rather than extending the Phase 6 `notification_event_type` enum

Business rules (Addendum §2.2, §2.3):
  - work_start_missed: recipient = user_id (self-targeted), Fixed Schedule mode
  - flexible_reminder_missed: recipient = user_id (self-targeted), Flexible mode
  - daily_hours_shortfall: one row per Admin/Manager in workspace (role-broadcast)
  - late_by_minutes set only for work_start_missed with late arrival
  - hours_logged set only for daily_hours_shortfall
"""

import uuid
from datetime import date, datetime
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey,
    Integer, Numeric, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AttendanceNotification(Base):
    __tablename__ = "attendance_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # The workspace this notification belongs to
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The subject Member (whose attendance is being tracked)
    # For shortfall: this is the Member who missed hours
    # For work_start_missed / flexible_reminder_missed: same as recipient_user_id
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # One of three attendance-specific notification types (Addendum §3.2)
    notification_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # The actual recipient of this notification row
    # For work_start_missed / flexible_reminder_missed: = user_id (self)
    # For daily_hours_shortfall: = each Admin/Manager in workspace (one row each)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The calendar day this notification concerns, in workspace timezone
    related_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Only set for work_start_missed when triggered by late arrival
    # Represents how many minutes late the Member was (Addendum §2.2)
    late_by_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Only set for daily_hours_shortfall — actual hours logged that day
    hours_logged: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[user_id]
    )
    recipient: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[recipient_user_id]
    )

    # ── Constraints ────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('work_start_missed', 'flexible_reminder_missed', 'daily_hours_shortfall')",
            name="ck_attendance_notif_type",
        ),
        CheckConstraint(
            "late_by_minutes IS NULL OR late_by_minutes >= 0",
            name="ck_attendance_late_minutes_non_negative",
        ),
        CheckConstraint(
            "hours_logged IS NULL OR hours_logged >= 0",
            name="ck_attendance_hours_non_negative",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AttendanceNotification id={self.id} "
            f"type={self.notification_type!r} "
            f"date={self.related_date}>"
        )
