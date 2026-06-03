import uuid
from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin

class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    hourly_rate_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Project", back_populates="client"
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_clients_workspace_id_name"),
        CheckConstraint("hourly_rate_cents >= 0", name="ck_clients_hourly_rate_cents"),
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name!r}>"
