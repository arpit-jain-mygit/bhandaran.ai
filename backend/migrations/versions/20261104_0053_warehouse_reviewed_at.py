# ---------------------------------------------------------------
# Add warehouse.reviewed_at: when an admin last approved or rejected it (M6).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0053_warehouse_reviewed_at
# Revises: 0052_warehouse_review_note
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0053_warehouse_reviewed_at"
down_revision: str | None = "0052_warehouse_review_note"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("warehouse", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("warehouse", "reviewed_at")
