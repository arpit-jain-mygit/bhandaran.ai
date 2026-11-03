# ---------------------------------------------------------------
# Create warehouse_stock_type: which stock types a warehouse accepts.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0046_create_warehouse_stock_type
# Revises: 0045_warehouse_owner_index
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0046_create_warehouse_stock_type"
down_revision: str | None = "0045_warehouse_owner_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "warehouse_stock_type",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("stock_type_id", sa.Uuid(), nullable=False),
        sa.UniqueConstraint("warehouse_id", "stock_type_id", name="uq_warehouse_stock_type"),
    )


def downgrade() -> None:
    op.drop_table("warehouse_stock_type")
