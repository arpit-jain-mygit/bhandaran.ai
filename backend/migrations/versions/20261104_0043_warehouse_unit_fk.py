# ---------------------------------------------------------------
# A warehouse's capacity unit must be a real unit (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0043_warehouse_unit_fk
# Revises: 0042_warehouse_city_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0043_warehouse_unit_fk"
down_revision: str | None = "0042_warehouse_city_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key("fk_warehouse_unit", "warehouse", "unit", ["unit_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_unit", "warehouse", type_="foreignkey")
