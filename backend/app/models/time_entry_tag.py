import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimeEntryTag(Base):
    """
    Many-to-many junction between time_entries and tags.
    DB Schema §4.12 — both FKs ON DELETE CASCADE.
    No timestamps on this table per DB Schema §4.12.
    """

    __tablename__ = "time_entry_tags"

    time_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("time_entries.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    time_entry: Mapped["TimeEntry"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TimeEntry", back_populates="tags"
    )
    tag: Mapped["Tag"] = relationship("Tag")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<TimeEntryTag entry={self.time_entry_id} tag={self.tag_id}>"
