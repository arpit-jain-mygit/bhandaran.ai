# ---------------------------------------------------------------
# Phone of a renter who has no account (for owner-only records).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0070_booking_renter_phone
# Revises: 0069_booking_renter_name
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0070_booking_renter_phone"
down_revision: str | None = "0069_booking_renter_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("booking", sa.Column("renter_phone", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("booking", "renter_phone")
