# ---------------------------------------------------------------
# Add app_user.email (login identity, M3 email OTP). Nullable for now:
# existing dev accounts get their emails before it is required.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0024_app_user_add_email
# Revises: 0023_otp_challenge_phone_index
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0024_app_user_add_email"
down_revision: str | None = "0023_otp_challenge_phone_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("email", sa.String(254), nullable=True))


def downgrade() -> None:
    op.drop_column("app_user", "email")
