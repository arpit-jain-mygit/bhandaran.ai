# ---------------------------------------------------------------
# Make app_user.phone optional: people log in by email, phone comes later (for bookings).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0025_app_user_phone_optional
# Revises: 0024_app_user_add_email
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0025_app_user_phone_optional"
down_revision: str | None = "0024_app_user_add_email"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("app_user", "phone", nullable=True)


def downgrade() -> None:
    op.alter_column("app_user", "phone", nullable=False)
