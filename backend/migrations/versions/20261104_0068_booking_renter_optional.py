# ---------------------------------------------------------------
# Booking renter is optional: an owner can record a booking for a
# renter who has no account (name and phone only). On DSQL, dropping
# NOT NULL is supported. One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0068_booking_renter_optional
# Revises: 0067_booking_owner_index
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0068_booking_renter_optional"
down_revision: str | None = "0067_booking_owner_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("booking", "renter_id", nullable=True)


def downgrade() -> None:
    # Only safe when every booking has a renter account.
    op.alter_column("booking", "renter_id", nullable=False)
