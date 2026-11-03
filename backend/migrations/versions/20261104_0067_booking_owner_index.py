# ---------------------------------------------------------------
# Index ix_booking_owner_created: an owner's bookings. On DSQL: CREATE INDEX ASYNC.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0067_booking_owner_index
# Revises: 0066_booking_renter_index
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0067_booking_owner_index"
down_revision: str | None = "0066_booking_renter_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_booking_owner_created", "booking", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_booking_owner_created", table_name="booking")
