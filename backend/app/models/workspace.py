"""
Workspace model — maps to `workspaces` table (DB Schema v2.0 §4.3).

Business rules enforced here:
  - rounding_interval_minutes IS NOT NULL when rounding_mode != 'none' (CHECK)
  - idle_timeout_minutes IS NOT NULL when idle_detection_enabled = TRUE (CHECK)
  - Soft-deleted via deleted_at; hard deletion by a scheduled job after 30 days
  - Cascades: all workspace-scoped tables ON DELETE CASCADE from this table
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, CHAR, CheckConstraint, DateTime,
    Enum, Integer, SmallInteger, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin
import enum


class RoundingMode(str, enum.Enum):
    none = "none"
    nearest = "nearest"
    up = "up"
    down = "down"


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_timezone: Mapped[str] = mapped_column(
        Text, nullable=False, default="UTC", server_default="UTC"
    )
    date_format: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="MM/DD/YYYY",
        server_default="MM/DD/YYYY",
    )
    currency: Mapped[str] = mapped_column(
        CHAR(3), nullable=False, default="USD", server_default="USD"
    )
    default_hourly_rate_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    rounding_mode: Mapped[str] = mapped_column(
        Enum("none", "nearest", "up", "down", name="rounding_mode", create_type=False),
        nullable=False,
        default="none",
        server_default="none",
    )
    rounding_interval_minutes: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    mandatory_description: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    max_timer_duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=86400, server_default="86400"
    )
    past_entry_limit_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=7, server_default="7"
    )
    lock_period_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=7, server_default="7"
    )
    approval_workflow_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    idle_detection_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    idle_timeout_minutes: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    members: Mapped[list["WorkspaceMember"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )

    # ── Constraints ────────────────────────────────────────────────────────
    __table_args__ = (
        # Rounding interval required when mode is not 'none'
        CheckConstraint(
            "rounding_mode = 'none' OR (rounding_mode != 'none' AND rounding_interval_minutes IS NOT NULL)",
            name="ck_workspace_rounding_consistency",
        ),
        # Idle timeout required when idle detection is enabled
        CheckConstraint(
            "idle_detection_enabled = FALSE OR (idle_detection_enabled = TRUE AND idle_timeout_minutes IS NOT NULL)",
            name="ck_workspace_idle_consistency",
        ),
        CheckConstraint(
            "rounding_interval_minutes IN (1,5,6,10,15,30) OR rounding_interval_minutes IS NULL",
            name="ck_workspace_rounding_interval",
        ),
        CheckConstraint(
            "idle_timeout_minutes IN (1,2,5,10,15) OR idle_timeout_minutes IS NULL",
            name="ck_workspace_idle_timeout",
        ),
        CheckConstraint(
            "default_hourly_rate_cents IS NULL OR default_hourly_rate_cents >= 0",
            name="ck_workspace_rate_non_negative",
        ),
        CheckConstraint(
            "max_timer_duration_seconds > 0",
            name="ck_workspace_max_timer_positive",
        ),
        CheckConstraint(
            "past_entry_limit_days >= 0",
            name="ck_workspace_past_entry_limit",
        ),
        CheckConstraint(
            "lock_period_days >= 0",
            name="ck_workspace_lock_period",
        ),
        CheckConstraint(
            "date_format IN ('MM/DD/YYYY','DD/MM/YYYY')",
            name="ck_workspace_date_format",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Workspace id={self.id} name={self.name!r}>"
