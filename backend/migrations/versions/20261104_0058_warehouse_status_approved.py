# ---------------------------------------------------------------
# Allow status APPROVED: an admin checked the listing (M6).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0058_warehouse_status_approved
# Revises: 0057_drop_warehouse_status_check
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0058_warehouse_status_approved"
down_revision: str | None = "0057_drop_warehouse_status_check"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_warehouse_status",
        "warehouse",
        "status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_warehouse_status", "warehouse", type_="check")
