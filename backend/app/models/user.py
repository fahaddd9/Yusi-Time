"""
User model — maps to the `users` table (DB Schema v2.2 §4.1).

Business rules enforced here:
  - email stored as-is; queried via LOWER(email) functional index
  - google_id is UNIQUE NULL (allows multiple non-Google accounts)
  - password_hash is NULL for Google-only accounts
  - is_active=False → cannot log in (set during anonymization)
  - is_superadmin=True → parallel bypass track, outside workspace_role enum.
    Never set by any endpoint. Only via direct DB access by a system operator.
  - Record is NEVER hard-deleted; anonymized in-place to preserve
    referential integrity on time_entries, audit_logs, etc.
"""

import uuid
from sqlalchemy import (
    Boolean, Index, SmallInteger, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(Text, nullable=True)
    weekly_hours_goal: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="TRUE")
    # DB Schema v2.2 — Super Admin flag.
    # NEVER set by any endpoint or workspace Admin. Only via direct DB access.
    # Always FALSE on every new account regardless of signup method (MASTER_PROMPT §11).
    is_superadmin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workspace_members: Mapped[list["WorkspaceMember"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "WorkspaceMember",
        back_populates="user",
        foreign_keys="[WorkspaceMember.user_id]",
        cascade="all, delete-orphan",
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )

    # ── Indexes ────────────────────────────────────────────────────────────
    __table_args__ = (
        # Case-insensitive lookup: SELECT * FROM users WHERE LOWER(email) = LOWER(:email)
        Index("ix_users_email_lower", func.lower("email")),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} active={self.is_active} superadmin={self.is_superadmin}>"
