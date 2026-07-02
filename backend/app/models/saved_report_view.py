"""
SavedReportView model — maps to `saved_report_views` table.

DB Schema v2.0 §4.15:
  - UUID primary key
  - workspace_id FK → workspaces (ON DELETE CASCADE)
  - user_id FK → users (ON DELETE CASCADE)
  - name TEXT NOT NULL
  - report_type TEXT NOT NULL CHECK (report_type IN ('summary', 'detailed', 'weekly'))
    NOTE: 'weekly' was added by DB Schema v2.1 migration §5 (migration 0002)
  - filters JSONB NOT NULL DEFAULT '{}'
  - created_at / updated_at maintained by trigger

UNIQUE constraint: (workspace_id, user_id, name)
  A user cannot have two saved views with the same name in the same workspace.

report_type allowed values (DB Schema v2.1 §5 — verified, DO NOT add new values):
  'summary' | 'detailed' | 'weekly'
"""

import uuid
from sqlalchemy import (
    CheckConstraint,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base, TimestampMixin


class SavedReportView(Base, TimestampMixin):
    """
    Stores a user's saved filter configuration for a report page.

    Private to the owner — never visible to other workspace members.
    PRD §3.8: "private to their account".

    report_type CHECK constraint values: 'summary' | 'detailed' | 'weekly'
    — DB Schema v2.1 §5 (migration 0002 added 'weekly')
    """

    __tablename__ = "saved_report_views"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        # ON DELETE CASCADE: views removed when workspace is hard-deleted
        UUID(as_uuid=True),
        __import__("sqlalchemy").ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        # ON DELETE CASCADE: views removed when user account is anonymized/deleted
        UUID(as_uuid=True),
        __import__("sqlalchemy").ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # DB Schema v2.1 §5 — CHECK constraint updated to include 'weekly'
    report_type: Mapped[str] = mapped_column(Text, nullable=False)
    # Serialized filter state (date range, project_ids, user_ids, billable, tags, group_by …)
    # DB Schema §4.15 — JSONB, NOT NULL, default empty object
    filters: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    __table_args__ = (
        # DB Schema v2.1 §5 — includes 'weekly' (migration 0002)
        CheckConstraint(
            "report_type IN ('summary', 'detailed', 'weekly')",
            name="ck_saved_report_views_report_type",
        ),
        # DB Schema §4.15 — unique name per user per workspace
        UniqueConstraint("workspace_id", "user_id", "name", name="uq_saved_report_views_name"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SavedReportView id={self.id} type={self.report_type!r} name={self.name!r}>"
