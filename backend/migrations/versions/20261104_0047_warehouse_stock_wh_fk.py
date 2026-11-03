# ---------------------------------------------------------------
# Stock-type link belongs to a warehouse (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0047_warehouse_stock_wh_fk
# Revises: 0046_create_warehouse_stock_type
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0047_warehouse_stock_wh_fk"
down_revision: str | None = "0046_create_warehouse_stock_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_warehouse_stock_type_warehouse",
        "warehouse_stock_type",
        "warehouse",
        ["warehouse_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_warehouse_stock_type_warehouse", "warehouse_stock_type", type_="foreignkey"
    )
