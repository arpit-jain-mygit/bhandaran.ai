# ---------------------------------------------------------------
# Add warehouse.reviewed_by_id: the admin who reviewed it (M6).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0054_warehouse_reviewed_by
# Revises: 0053_warehouse_reviewed_at
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0054_warehouse_reviewed_by"
down_revision: str | None = "0053_warehouse_reviewed_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("warehouse", sa.Column("reviewed_by_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("warehouse", "reviewed_by_id")
