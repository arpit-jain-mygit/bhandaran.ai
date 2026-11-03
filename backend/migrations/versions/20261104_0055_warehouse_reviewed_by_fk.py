# ---------------------------------------------------------------
# The reviewer must be a real user (FK, NOT VALID on DSQL).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0055_warehouse_reviewed_by_fk
# Revises: 0054_warehouse_reviewed_by
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0055_warehouse_reviewed_by_fk"
down_revision: str | None = "0054_warehouse_reviewed_by"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_warehouse_reviewed_by", "warehouse", "app_user", ["reviewed_by_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_warehouse_reviewed_by", "warehouse", type_="foreignkey")
