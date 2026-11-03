# ---------------------------------------------------------------
# Allow status UNCLAIMED: a renter invited by an owner, not yet claimed (M4).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0038_app_user_status_unclaimed
# Revises: 0037_drop_app_user_status_check
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0038_app_user_status_unclaimed"
down_revision: str | None = "0037_drop_app_user_status_check"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_app_user_status",
        "app_user",
        "status IN ('ACTIVE', 'SUSPENDED', 'UNCLAIMED')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_app_user_status", "app_user", type_="check")
