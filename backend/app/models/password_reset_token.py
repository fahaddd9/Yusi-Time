"""
PasswordResetToken model — maps to `password_reset_tokens` table (DB Schema v2.0 §4.2).

Business rules:
  - token is a secrets.token_urlsafe(32) — never logged
  - expires_at = created_at + 1 hour (enforced in auth_service)
  - used=True marks the token as consumed — rejected on next attempt
  - New reset request deletes all prior tokens for the same user (auth_service)
  - Cascades on user deletion (ON DELETE CASCADE)
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="password_reset_tokens"
    )

    # ── Constraints ────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_prt_expires_after_created"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PasswordResetToken user_id={self.user_id} used={self.used}>"
