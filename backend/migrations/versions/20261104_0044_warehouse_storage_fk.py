# ---------------------------------------------------------------
# A warehouse's storage type must be a real storage type (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0044_warehouse_storage_fk
# Revises: 0043_warehouse_unit_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0044_warehouse_storage_fk"
down_revision: str | None = "0043_warehouse_unit_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_warehouse_storage_type", "warehouse", "storage_type", ["storage_type_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_storage_type", "warehouse", type_="foreignkey")
