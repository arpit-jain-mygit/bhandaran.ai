# ---------------------------------------------------------------
# Index ix_booking_renter_created: a renter's bookings. On DSQL: CREATE INDEX ASYNC.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0066_booking_renter_index
# Revises: 0065_booking_warehouse_index
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0066_booking_renter_index"
down_revision: str | None = "0065_booking_warehouse_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_booking_renter_created", "booking", ["renter_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_booking_renter_created", table_name="booking")
