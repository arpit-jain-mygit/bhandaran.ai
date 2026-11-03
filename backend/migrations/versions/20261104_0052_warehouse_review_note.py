# ---------------------------------------------------------------
# Add warehouse.review_note: the admin's reason when a listing is sent back (M6).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0052_warehouse_review_note
# Revises: 0050_warehouse_photo_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0052_warehouse_review_note"
down_revision: str | None = "0050_warehouse_photo_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("warehouse", sa.Column("review_note", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("warehouse", "review_note")
