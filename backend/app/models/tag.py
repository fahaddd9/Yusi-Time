import uuid
from datetime import datetime
from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str | None] = mapped_column(CHAR(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_tags_workspace_id_name"),
        CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_tags_color"),
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"
