# ---------------------------------------------------------------
# Index app_user.email so each email has one account (unique).
# On DSQL the dialect creates it with CREATE UNIQUE INDEX ASYNC.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0026_app_user_email_unique
# Revises: 0025_app_user_phone_optional
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0026_app_user_email_unique"
down_revision: str | None = "0025_app_user_phone_optional"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("uq_app_user_email", "app_user", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_app_user_email", table_name="app_user")
