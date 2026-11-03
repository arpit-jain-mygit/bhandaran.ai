# ---------------------------------------------------------------
# Add app_user.city_id: the owner's or renter's city (profile, M4).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0030_app_user_city
# Revises: 0029_otp_challenge_email_index
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0030_app_user_city"
down_revision: str | None = "0029_otp_challenge_email_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("city_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_user", "city_id")
