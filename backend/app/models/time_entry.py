import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class TimeEntry(Base, TimestampMixin):
    """
    Core time tracking record.
    Status drives all locking, approval, and editability rules.
    DB Schema §4.11 — three CHECK constraints enforced below.
    duration_seconds stores ROUNDED seconds only — raw is never persisted (PRD §3.3.4).
    """

    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="TRUE")
    status: Mapped[str] = mapped_column(
        # DB Schema §3 — entry_status enum (draft, running, pending, approved)
        Enum("draft", "running", "pending", "approved", name="entry_status", create_type=False),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        # TIMESTAMPTZ stored as UTC
        __import__("sqlalchemy").DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        __import__("sqlalchemy").DateTime(timezone=True),
        nullable=True,
    )
    # Rounded duration in seconds — NEVER stores raw seconds (PRD §3.3.4)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Snapshot of effective rate at moment of save — immutable after write (PRD §5 Rate Snapshot)
    hourly_rate_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Computed and stored: ROUND((duration_seconds / 3600.0) * hourly_rate_cents)
    billable_amount_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]  # noqa: F821
    project: Mapped["Project"] = relationship("Project")  # type: ignore[name-defined]  # noqa: F821
    task: Mapped["Task"] = relationship("Task")  # type: ignore[name-defined]  # noqa: F821
    tags: Mapped[list["TimeEntryTag"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TimeEntryTag", back_populates="time_entry", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # DB Schema §4.11 CHECK 1 — end_time must be after start_time when both present
        CheckConstraint(
            "end_time IS NULL OR end_time > start_time",
            name="ck_time_entries_end_after_start",
        ),
        # DB Schema §4.11 CHECK 2 — running entries must not have end_time or duration
        CheckConstraint(
            "status != 'running' OR (status = 'running' AND end_time IS NULL AND duration_seconds IS NULL)",
            name="ck_time_entries_running_no_end",
        ),
        # DB Schema §4.11 CHECK 3 — completed non-draft entries must have end_time and duration
        CheckConstraint(
            "status = 'running' OR status = 'draft' OR (end_time IS NOT NULL AND duration_seconds IS NOT NULL)",
            name="ck_time_entries_completed_has_end",
        ),
        CheckConstraint("duration_seconds >= 0", name="ck_time_entries_duration_non_negative"),
        CheckConstraint("hourly_rate_cents >= 0", name="ck_time_entries_hourly_rate_non_negative"),
        CheckConstraint("billable_amount_cents >= 0", name="ck_time_entries_billable_amount_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<TimeEntry id={self.id} status={self.status!r} user_id={self.user_id}>"
