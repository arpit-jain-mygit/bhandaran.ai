# ---------------------------------------------------------------
# Name of a renter who has no account (for owner-only records).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0069_booking_renter_name
# Revises: 0068_booking_renter_optional
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0069_booking_renter_name"
down_revision: str | None = "0068_booking_renter_optional"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("booking", sa.Column("renter_name", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("booking", "renter_name")
