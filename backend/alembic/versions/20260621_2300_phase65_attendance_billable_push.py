"""phase_65_attendance_billable_push

Revision ID: 20260621_2300
Revises: 20260603_1200
Create Date: 2026-06-21

Phase 6.5 — Attendance, Daily Hour Targets, Billable Toggle & Push Subscriptions.

Changes:
  1. `workspaces` table: 6 new columns (Addendum §3.1)
       - attendance_enabled BOOLEAN NOT NULL DEFAULT false
       - attendance_mode VARCHAR NOT NULL DEFAULT 'fixed_schedule'
         CHECK IN ('fixed_schedule', 'flexible_hours')
       - work_start_time TIME NULL
       - daily_required_hours NUMERIC(4,2) NULL  CHECK > 0 when not NULL
       - off_days INTEGER[] NOT NULL DEFAULT {0}
       - is_billable BOOLEAN NOT NULL DEFAULT true
  2. New table `attendance_notifications` (Addendum §3.2)
       - Separate from general notifications table; supports self-targeted
         and role-broadcast attendance notification types with typed fields
  3. New table `push_subscriptions` (Addendum §3.3)
       - Per-user, per-browser Web Push subscription storage for F1 push delivery

This is a HAND-WRITTEN migration following the pattern established in Phase 1.5
(Architecture Decisions Log, 2026-05-31). We do NOT use autogenerate because
the DB may contain future-phase tables not yet in our models.

downgrade() cleanly reverses all changes in the correct dependency order.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision: str = "20260621_2300"
down_revision: Union[str, None] = "20260603_1200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    1. Add 6 new columns to workspaces table (Addendum §3.1).
       All columns have defaults that preserve existing workspace behavior —
       attendance_enabled=false means no triggers fire on existing workspaces,
       is_billable=true preserves all existing billable behavior (PRD-ADD-05).

    2. Create attendance_notifications table (Addendum §3.2).
       Uses a TEXT column with CHECK constraint for notification_type rather
       than a native enum, consistent with VARCHAR+CHECK pattern noted in §3.1.

    3. Create push_subscriptions table (Addendum §3.3).
       Unique constraint (user_id, endpoint) prevents duplicate browser registrations.
    """

    # ── 1. Add new columns to workspaces ────────────────────────────────────
    # Addendum §3.1 — all additive, all with safe defaults preserving existing behavior
    op.add_column(
        "workspaces",
        sa.Column(
            "attendance_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "attendance_mode",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'fixed_schedule'"),
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "work_start_time",
            sa.Time(timezone=False),
            nullable=True,
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "daily_required_hours",
            sa.Numeric(4, 2),
            nullable=True,
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "off_days",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{0}'"),
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "is_billable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
            # Default TRUE: existing workspaces remain billable (PRD-ADD-05)
        ),
    )

    # CHECK constraints for the new workspaces columns
    op.create_check_constraint(
        "ck_workspace_attendance_mode",
        "workspaces",
        "attendance_mode IN ('fixed_schedule', 'flexible_hours')",
    )
    op.create_check_constraint(
        "ck_workspace_daily_hours_positive",
        "workspaces",
        "daily_required_hours IS NULL OR daily_required_hours > 0",
    )

    # ── 2. Create attendance_notifications table ─────────────────────────────
    # Addendum §3.2 — dedicated table for attendance-specific notification types
    # that cannot be cleanly represented by the existing general notifications table
    op.create_table(
        "attendance_notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_type", sa.Text(), nullable=False),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_date", sa.Date(), nullable=False),
        sa.Column("late_by_minutes", sa.Integer(), nullable=True),
        sa.Column("hours_logged", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),

        # Foreign keys
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"], ["users.id"], ondelete="CASCADE"
        ),

        # CHECK constraints (Addendum §3.2)
        sa.CheckConstraint(
            "notification_type IN ('work_start_missed', 'flexible_reminder_missed', 'daily_hours_shortfall')",
            name="ck_attendance_notif_type",
        ),
        sa.CheckConstraint(
            "late_by_minutes IS NULL OR late_by_minutes >= 0",
            name="ck_attendance_late_minutes_non_negative",
        ),
        sa.CheckConstraint(
            "hours_logged IS NULL OR hours_logged >= 0",
            name="ck_attendance_hours_non_negative",
        ),
    )

    # Indexes for attendance_notifications (Addendum §3.2)
    op.create_index(
        "idx_attendance_notif_recipient",
        "attendance_notifications",
        ["recipient_user_id", "is_read"],
    )
    op.create_index(
        "idx_attendance_notif_workspace_date",
        "attendance_notifications",
        ["workspace_id", "related_date"],
    )
    op.create_index(
        "idx_attendance_notif_user_date",
        "attendance_notifications",
        ["user_id", "related_date"],
    )

    # ── 3. Create push_subscriptions table ───────────────────────────────────
    # Addendum §3.3 — Web Push subscription storage for F1 push delivery
    op.create_table(
        "push_subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh_key", sa.Text(), nullable=False),
        sa.Column("auth_key", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),

        # Foreign key
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),

        # Unique constraint: one subscription per user+endpoint pair
        sa.UniqueConstraint(
            "user_id", "endpoint",
            name="uq_push_subscriptions_user_endpoint",
        ),
    )

    op.create_index(
        "idx_push_subscriptions_user",
        "push_subscriptions",
        ["user_id"],
    )


def downgrade() -> None:
    """
    Reverse all Phase 6.5 schema changes.

    Order: drop dependent tables first (push_subscriptions, attendance_notifications),
    then drop the columns and constraints from workspaces.
    """

    # Drop new tables
    op.drop_index("idx_push_subscriptions_user", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")

    op.drop_index("idx_attendance_notif_user_date",      table_name="attendance_notifications")
    op.drop_index("idx_attendance_notif_workspace_date", table_name="attendance_notifications")
    op.drop_index("idx_attendance_notif_recipient",      table_name="attendance_notifications")
    op.drop_table("attendance_notifications")

    # Drop CHECK constraints from workspaces before dropping columns
    op.drop_constraint("ck_workspace_daily_hours_positive", "workspaces", type_="check")
    op.drop_constraint("ck_workspace_attendance_mode",      "workspaces", type_="check")

    # Drop the 6 new workspaces columns
    op.drop_column("workspaces", "is_billable")
    op.drop_column("workspaces", "off_days")
    op.drop_column("workspaces", "daily_required_hours")
    op.drop_column("workspaces", "work_start_time")
    op.drop_column("workspaces", "attendance_mode")
    op.drop_column("workspaces", "attendance_enabled")
