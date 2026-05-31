"""add_is_superadmin_to_users

Revision ID: 20260531_1500
Revises: 20260526_1000
Create Date: 2026-05-31

Adds the `is_superadmin` boolean column to the `users` table.
DB Schema v2.2 · MASTER_PROMPT §11 · Phase 1.5

This is a targeted, hand-written migration. We do NOT use autogenerate here
because the existing DB contains Phase 2+ tables that do not yet have
corresponding SQLAlchemy models — autogenerate would incorrectly try to drop
them. This migration adds only the single column needed.

RULE B-12: Migration is reversible. downgrade() removes the column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "20260531_1500"
down_revision: Union[str, None] = "20260526_1000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add is_superadmin column to users table.

    - NOT NULL with DEFAULT FALSE so no backfill is needed.
    - All existing rows automatically get FALSE (correct — no existing
      Super Admin accounts exist before this migration).
    - No endpoint, no workspace Admin, no API can set this to TRUE.
      Only a direct DB UPDATE by a system operator does so.
    """
    op.add_column(
        "users",
        sa.Column(
            "is_superadmin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )


def downgrade() -> None:
    """Remove the is_superadmin column (fully reversible per RULE B-12)."""
    op.drop_column("users", "is_superadmin")
