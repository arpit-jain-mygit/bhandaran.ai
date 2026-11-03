# ---------------------------------------------------------------
# A warehouse's city must be a real city (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0042_warehouse_city_fk
# Revises: 0041_warehouse_owner_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0042_warehouse_city_fk"
down_revision: str | None = "0041_warehouse_owner_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key("fk_warehouse_city", "warehouse", "city", ["city_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_city", "warehouse", type_="foreignkey")
