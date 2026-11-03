# ---------------------------------------------------------------
# Drop the status CHECK so UNCLAIMED can be added (M4).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0037_drop_app_user_status_check
# Revises: 0036_validate_user_invited_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0037_drop_app_user_status_check"
down_revision: str | None = "0036_validate_user_invited_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_app_user_status", "app_user", type_="check")


def downgrade() -> None:
    op.create_check_constraint(
        "ck_app_user_status", "app_user", "status IN ('ACTIVE', 'SUSPENDED')"
    )
