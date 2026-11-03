# ---------------------------------------------------------------
# A photo belongs to a warehouse (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0050_warehouse_photo_fk
# Revises: 0049_create_warehouse_photo
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0050_warehouse_photo_fk"
down_revision: str | None = "0049_create_warehouse_photo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_warehouse_photo_warehouse", "warehouse_photo", "warehouse", ["warehouse_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_photo_warehouse", "warehouse_photo", type_="foreignkey")
