import uuid
from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SubmissionEntry(Base):
    """
    Submission Entry junction model.
    DB Schema §4.14.
    """
    __tablename__ = "submission_entries"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("timesheet_submissions.id", ondelete="CASCADE"), primary_key=True
    )
    time_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("time_entries.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    submission: Mapped["TimesheetSubmission"] = relationship("TimesheetSubmission", back_populates="entries")  # type: ignore[name-defined] # noqa: F821
    time_entry: Mapped["TimeEntry"] = relationship("TimeEntry")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("uq_submission_entries_one_per_entry", "time_entry_id", unique=True),
    )
