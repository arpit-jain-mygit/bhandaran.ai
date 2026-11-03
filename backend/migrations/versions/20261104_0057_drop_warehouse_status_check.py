# ---------------------------------------------------------------
# Drop the status CHECK so APPROVED can be added (M6).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0057_drop_warehouse_status_check
# Revises: 0056_validate_wh_reviewed_by
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0057_drop_warehouse_status_check"
down_revision: str | None = "0056_validate_wh_reviewed_by"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_warehouse_status", "warehouse", type_="check")


def downgrade() -> None:
    op.create_check_constraint(
        "ck_warehouse_status", "warehouse", "status IN ('DRAFT', 'PENDING_REVIEW')"
    )
