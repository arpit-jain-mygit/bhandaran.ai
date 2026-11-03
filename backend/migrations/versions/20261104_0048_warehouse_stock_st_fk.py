# ---------------------------------------------------------------
# Stock-type link points at a real stock type (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0048_warehouse_stock_st_fk
# Revises: 0047_warehouse_stock_wh_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0048_warehouse_stock_st_fk"
down_revision: str | None = "0047_warehouse_stock_wh_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_warehouse_stock_type_stock",
        "warehouse_stock_type",
        "stock_type",
        ["stock_type_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_stock_type_stock", "warehouse_stock_type", type_="foreignkey")
