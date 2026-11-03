# ---------------------------------------------------------------
# Add app_user.invited_by_id: the owner who invited an unclaimed renter (M4).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0032_app_user_invited_by
# Revises: 0031_app_user_gst
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0032_app_user_invited_by"
down_revision: str | None = "0031_app_user_gst"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("invited_by_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_user", "invited_by_id")
