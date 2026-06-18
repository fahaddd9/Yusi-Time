"""add_time_entries_and_time_entry_tags

Revision ID: 20260603_1200
Revises: 20260531_1500
Create Date: 2026-06-03

Adds the `time_entries` and `time_entry_tags` tables for Phase 4 — Time Tracking Core.
DB Schema v2.0 §4.11 (time_entries) and §4.12 (time_entry_tags).

This is a hand-written migration. We do NOT use autogenerate because the DB
contains future-phase tables that are not yet in our models — autogenerate
would incorrectly flag them for deletion.

Migration also creates the `entry_status` PostgreSQL enum if it does not yet
exist (it may have been created by the initial schema migration on the live DB).

RULE B-12: Migration is reversible. downgrade() drops both tables and the enum.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision: str = "20260603_1200"
down_revision: Union[str, None] = "20260531_1500"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create time_entries and time_entry_tags tables.

    entry_status enum:  draft | running | pending | approved
    (DB Schema §3 — 'rejected' is NOT in this enum; it belongs on submission_status only)

    Three CHECK constraints on time_entries per DB Schema §4.11:
      1. end_time IS NULL OR end_time > start_time
      2. Running entries must not have end_time or duration_seconds
      3. Non-draft, non-running entries must have both end_time and duration_seconds

    Partial unique index: one running timer per user per workspace (DB Schema §4.11 business rule).
    All monetary columns use BIGINT (DB Schema §9).
    """

    # Create entry_status enum if it does not yet exist
    # (the initial schema migration may have created it already)
    postgresql.ENUM(
        "draft", "running", "pending", "approved",
        name="entry_status",
        create_type=False,   # don't create automatically — we check below
    )
    op.execute(
        "DO $$ BEGIN "
        "  CREATE TYPE entry_status AS ENUM ('draft', 'running', 'pending', 'approved'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    # ── time_entries ──────────────────────────────────────────────────────────
    op.create_table(
        "time_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("billable", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("status",
                  sa.Enum("draft", "running", "pending", "approved",
                          name="entry_status", create_type=False),
                  nullable=False, server_default=sa.text("'draft'")),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("hourly_rate_cents", sa.BigInteger(), nullable=True),
        sa.Column("billable_amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),

        # Foreign keys
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"],      ["users.id"],       ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"],   ["projects.id"],    ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["task_id"],       ["tasks.id"],       ondelete="SET NULL"),

        # CHECK constraints (DB Schema §4.11)
        sa.CheckConstraint(
            "end_time IS NULL OR end_time > start_time",
            name="ck_time_entries_end_after_start",
        ),
        sa.CheckConstraint(
            "status != 'running' OR (status = 'running' AND end_time IS NULL AND duration_seconds IS NULL)",
            name="ck_time_entries_running_no_end",
        ),
        sa.CheckConstraint(
            "status = 'running' OR status = 'draft' OR (end_time IS NOT NULL AND duration_seconds IS NOT NULL)",
            name="ck_time_entries_completed_has_end",
        ),
        sa.CheckConstraint("duration_seconds >= 0",        name="ck_time_entries_duration_non_negative"),
        sa.CheckConstraint("hourly_rate_cents >= 0",       name="ck_time_entries_hourly_rate_non_negative"),
        sa.CheckConstraint("billable_amount_cents >= 0",   name="ck_time_entries_billable_amount_non_negative"),
    )

    # Standard indexes
    op.create_index("ix_time_entries_workspace_id", "time_entries", ["workspace_id"])
    op.create_index("ix_time_entries_user_id",      "time_entries", ["user_id"])
    op.create_index("ix_time_entries_project_id",   "time_entries", ["project_id"])
    op.create_index("ix_time_entries_status",       "time_entries", ["status"])
    op.create_index("ix_time_entries_start_time",   "time_entries", ["start_time"])

    # Partial unique index: one running timer per user per workspace
    # (DB Schema §4.11 business rule — enforced at DB layer too)
    op.create_index(
        "uq_time_entries_one_running_per_user",
        "time_entries",
        ["workspace_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
    )

    # updated_at trigger
    op.execute(
        "CREATE TRIGGER set_time_entries_updated_at "
        "BEFORE UPDATE ON time_entries "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )

    # ── time_entry_tags ───────────────────────────────────────────────────────
    op.create_table(
        "time_entry_tags",
        sa.Column("time_entry_id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("tag_id",        postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),

        sa.ForeignKeyConstraint(["time_entry_id"], ["time_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"],         ["tags.id"],         ondelete="CASCADE"),
    )


def downgrade() -> None:
    """
    Drop time_entry_tags, then time_entries.
    The entry_status enum is NOT dropped because it may be used by other tables
    in a live database or partial rollback scenario. Drop it manually if needed.
    """
    op.drop_table("time_entry_tags")
    op.drop_index("uq_time_entries_one_running_per_user", table_name="time_entries")
    op.drop_index("ix_time_entries_start_time",   table_name="time_entries")
    op.drop_index("ix_time_entries_status",       table_name="time_entries")
    op.drop_index("ix_time_entries_project_id",   table_name="time_entries")
    op.drop_index("ix_time_entries_user_id",      table_name="time_entries")
    op.drop_index("ix_time_entries_workspace_id", table_name="time_entries")
    op.drop_table("time_entries")
    # Optionally drop enum — safe to do only if no other tables use it
    # op.execute("DROP TYPE IF EXISTS entry_status;")
