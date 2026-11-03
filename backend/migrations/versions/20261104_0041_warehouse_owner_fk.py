# ---------------------------------------------------------------
# A warehouse belongs to an existing user (FK).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0041_warehouse_owner_fk
# Revises: 0040_create_warehouse
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0041_warehouse_owner_fk"
down_revision: str | None = "0040_create_warehouse"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key("fk_warehouse_owner", "warehouse", "app_user", ["owner_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_owner", "warehouse", type_="foreignkey")
