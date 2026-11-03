# ---------------------------------------------------------------
# booking.stock_type_id must point at a real stock_type row (FK). The table is new,
# so there are no existing rows to validate.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0064_booking_stock_type_fk
# Revises: 0063_booking_renter_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0064_booking_stock_type_fk"
down_revision: str | None = "0063_booking_renter_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_booking_stock_type", "booking", "stock_type", ["stock_type_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_booking_stock_type", "booking", type_="foreignkey")
