"""
Invite model — maps to the `invites` table (DB Schema v2.0 §4.5).

Business rules enforced here:
  - role cannot be 'admin' (enforced at DB CHECK + service layer)
  - expires_at must be > created_at
  - used=True requires used_at IS NOT NULL (and vice versa)
  - revoked=True requires revoked_at IS NOT NULL (and vice versa)
  - cannot be both used AND revoked
  - ON DELETE CASCADE from workspace — invites die with their workspace
  - ON DELETE RESTRICT from created_by_user — inviter must exist
  - ON DELETE SET NULL from used_by_user — keeps record even if recipient is anonymized
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("admin", "manager", "member", "viewer", name="workspace_role", create_type=False),
        nullable=False,
        default="member",
        server_default="member",
    )
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        # Default: 7 days from now (set by service layer, not server_default)
    )
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="FALSE")
    used_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="FALSE")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Workspace", foreign_keys=[workspace_id]
    )
    created_by: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[created_by_user_id]
    )
    used_by: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[used_by_user_id]
    )

    # ── Constraints (mirrors DB Schema §4.5) ──────────────────────────────
    __table_args__ = (
        # role cannot be admin
        CheckConstraint(
            "role IN ('manager', 'member', 'viewer')",
            name="ck_invites_role_not_admin",
        ),
        # expires_at must be after created_at
        CheckConstraint("expires_at > created_at", name="ck_inv_expires"),
        # used=True ↔ used_at IS NOT NULL
        CheckConstraint(
            "(used = TRUE AND used_at IS NOT NULL) OR (used = FALSE AND used_at IS NULL)",
            name="ck_inv_used",
        ),
        # revoked=True ↔ revoked_at IS NOT NULL
        CheckConstraint(
            "(revoked = TRUE AND revoked_at IS NOT NULL) OR (revoked = FALSE AND revoked_at IS NULL)",
            name="ck_inv_revoked",
        ),
        # cannot be both used and revoked
        CheckConstraint(
            "NOT (used = TRUE AND revoked = TRUE)",
            name="ck_inv_not_both",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Invite id={self.id} workspace={self.workspace_id} "
            f"email={self.email!r} role={self.role!r} used={self.used} revoked={self.revoked}>"
        )
