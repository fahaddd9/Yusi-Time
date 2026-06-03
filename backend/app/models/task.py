import uuid
from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin

class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    estimated_hours: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    billable_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hourly_rate_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")  # type: ignore[name-defined]  # noqa: F821

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_tasks_project_id_name"),
        CheckConstraint("estimated_hours > 0", name="ck_tasks_estimated_hours"),
        CheckConstraint("hourly_rate_cents >= 0", name="ck_tasks_hourly_rate_cents"),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} name={self.name!r}>"
