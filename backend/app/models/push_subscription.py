"""
PushSubscription model — maps to `push_subscriptions` table.

Addendum §3.3 — required for F1 browser push delivery (Web Push protocol).

Business rules:
  - A user may have multiple subscriptions (multiple browsers/devices/profiles)
  - All active subscriptions for a user receive the push on trigger
  - Unique constraint on (user_id, endpoint) prevents duplicate registrations
    for the same browser profile
  - Deleted with user via CASCADE (privacy: no push to deleted users)
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

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
    # The push service endpoint URL (browser-specific, unique per subscription)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    # ECDH public key for payload encryption (base64url-encoded)
    p256dh_key: Mapped[str] = mapped_column(Text, nullable=False)
    # Authentication secret (base64url-encoded)
    auth_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[user_id]
    )

    # ── Constraints ────────────────────────────────────────────────────────
    __table_args__ = (
        # Prevents duplicate subscriptions for the same browser profile
        UniqueConstraint("user_id", "endpoint", name="uq_push_subscriptions_user_endpoint"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PushSubscription id={self.id} user_id={self.user_id}>"
