"""
AuditLog model — maps to the `audit_logs` table (DB Schema v2.0 §4.19).

Business rules:
  - Append-only. No UPDATE or DELETE ever issued against this table.
  - workspace_id is nullable (platform-level events may have no workspace)
  - actor_user_id is nullable (system events with no human actor)
  - ON DELETE SET NULL for both FK refs — preserves audit trail even after
    workspace soft-deletion or user anonymization
  - old_values / new_values stored as JSONB for flexibility
  - ip_address and user_agent captured for security events
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        Enum(
            "create", "update", "delete", "approve", "reject", "submit",
            "lock_override", "role_change", "invite_generated", "invite_revoked",
            "workspace_soft_deleted",
            name="audit_action",
            create_type=False,
        ),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workspace: Mapped["Workspace | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Workspace", foreign_keys=[workspace_id]
    )
    actor: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[actor_user_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"entity_type={self.entity_type!r} actor={self.actor_user_id}>"
        )
