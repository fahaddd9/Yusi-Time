"""
WorkspaceMember model — maps to `workspace_members` table (DB Schema v2.0 §4.4).

Business rules:
  - Composite PK (workspace_id, user_id) prevents duplicate memberships
  - ON DELETE CASCADE from workspace — if workspace is deleted, memberships go too
  - ON DELETE RESTRICT from user — membership must be removed before anonymization
  - ON DELETE SET NULL for invited_by_user_id — keeps record even if inviter is anonymized
  - Application must prevent removal of the last admin in a workspace
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        Enum("admin", "manager", "member", "viewer", name="workspace_role", create_type=False),
        nullable=False,
        default="member",
        server_default="member",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Workspace", back_populates="members"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[user_id],
        back_populates="workspace_members",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WorkspaceMember workspace={self.workspace_id} user={self.user_id} role={self.role!r}>"
