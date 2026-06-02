"""
Notification model — maps to the `notifications` table (DB Schema v2.0 §4.18).

Business rules:
  - Created by service layer; never by user input
  - read_at IS NULL → unread. Set read_at to mark read.
  - ON DELETE CASCADE from workspace and user — notifications die with context
  - metadata is JSONB for event-specific payload (e.g. workspace name, reviewer info)
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        Enum(
            "timesheet_submitted", "timesheet_approved", "timesheet_rejected",
            "timer_auto_stopped", "workspace_deleted",
            name="notification_event_type",
            create_type=False,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Notification id={self.id} user={self.user_id} "
            f"event={self.event_type!r} read={self.read_at is not None}>"
        )
