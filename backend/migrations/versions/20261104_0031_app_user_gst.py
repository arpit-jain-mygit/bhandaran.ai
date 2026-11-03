# ---------------------------------------------------------------
# Add app_user.gst_number: optional GST number (profile, M4).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0031_app_user_gst
# Revises: 0030_app_user_city
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0031_app_user_gst"
down_revision: str | None = "0030_app_user_city"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("gst_number", sa.String(15), nullable=True))


def downgrade() -> None:
    op.drop_column("app_user", "gst_number")
