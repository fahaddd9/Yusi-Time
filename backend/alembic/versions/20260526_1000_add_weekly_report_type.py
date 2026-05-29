"""add weekly report type

Revision ID: 20260526_1000
Revises: 20260526_0900
Create Date: 2026-05-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260526_1000'
down_revision: Union[str, None] = '20260526_0900'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE saved_report_views DROP CONSTRAINT IF EXISTS saved_report_views_report_type_check")
    op.execute("ALTER TABLE saved_report_views ADD CONSTRAINT saved_report_views_report_type_check CHECK (report_type IN ('summary', 'detailed', 'weekly'))")

def downgrade() -> None:
    op.execute("ALTER TABLE saved_report_views DROP CONSTRAINT IF EXISTS saved_report_views_report_type_check")
    op.execute("ALTER TABLE saved_report_views ADD CONSTRAINT saved_report_views_report_type_check CHECK (report_type IN ('summary', 'detailed'))")
