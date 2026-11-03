# ---------------------------------------------------------------
# booking.renter_id must point at a real app_user row (FK). The table is new,
# so there are no existing rows to validate.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0063_booking_renter_fk
# Revises: 0062_booking_owner_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0063_booking_renter_fk"
down_revision: str | None = "0062_booking_owner_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key("fk_booking_renter", "booking", "app_user", ["renter_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_booking_renter", "booking", type_="foreignkey")
