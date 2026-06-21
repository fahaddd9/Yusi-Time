import uuid
from datetime import date, datetime
from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin

class TimesheetSubmission(Base, TimestampMixin):
    """
    Timesheet Submission model.
    DB Schema §4.13.
    """
    __tablename__ = "timesheet_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="submission_status", create_type=False),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        __import__("sqlalchemy").DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        __import__("sqlalchemy").DateTime(timezone=True), nullable=True
    )
    rejection_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")  # type: ignore[name-defined] # noqa: F821
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore[name-defined] # noqa: F821
    reviewed_by: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by_user_id])  # type: ignore[name-defined] # noqa: F821
    entries: Mapped[list["SubmissionEntry"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        "SubmissionEntry", back_populates="submission", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("EXTRACT(DOW FROM week_start) = 1", name="chk_ts_week_is_monday"),
        CheckConstraint(
            "status != 'rejected' OR (rejection_note IS NOT NULL AND TRIM(rejection_note) != '')",
            name="chk_ts_rejection_note",
        ),
        CheckConstraint(
            "(status = 'pending' AND reviewed_at IS NULL) OR (status != 'pending' AND reviewed_at IS NOT NULL)",
            name="chk_ts_reviewed_at",
        ),
        Index(
            "uq_timesheet_submissions_one_pending",
            "workspace_id", "user_id", "week_start",
            unique=True,
            postgresql_where=text("status = 'pending'")
        ),
        Index("ix_timesheet_submissions_workspace_status", "workspace_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<TimesheetSubmission id={self.id} status={self.status!r}>"
