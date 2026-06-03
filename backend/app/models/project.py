import uuid
import enum
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CHAR, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin

class ProjectVisibility(str, enum.Enum):
    public = "public"
    private = "private"

class ProjectStatus(str, enum.Enum):
    active = "active"
    archived = "archived"

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    default_billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="TRUE")
    budget_hours: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_amount_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    visibility: Mapped[str] = mapped_column(
        Enum("public", "private", name="project_visibility", create_type=False),
        nullable=False,
        default="public",
        server_default="public",
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "archived", name="project_status", create_type=False),
        nullable=False,
        default="active",
        server_default="active",
    )
    hourly_rate_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    color: Mapped[str | None] = mapped_column(CHAR(7), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="projects")  # type: ignore[name-defined]  # noqa: F821
    members: Mapped[list["ProjectMember"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_projects_workspace_id_name"),
        CheckConstraint("budget_hours > 0", name="ck_projects_budget_hours"),
        CheckConstraint("budget_amount_cents > 0", name="ck_projects_budget_amount_cents"),
        CheckConstraint("hourly_rate_cents >= 0", name="ck_projects_hourly_rate_cents"),
        CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_projects_color"),
        CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR (status = 'active' AND archived_at IS NULL)",
            name="ck_projects_status_archived_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"
