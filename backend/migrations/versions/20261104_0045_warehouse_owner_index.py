# ---------------------------------------------------------------
# Index warehouse (owner_id, created_at): an owner's list of listings.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0045_warehouse_owner_index
# Revises: 0044_warehouse_storage_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0045_warehouse_owner_index"
down_revision: str | None = "0044_warehouse_storage_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_warehouse_owner_created", "warehouse", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_warehouse_owner_created", table_name="warehouse")
