# ---------------------------------------------------------------
# Index ix_booking_warehouse_dates: capacity checks and free space for a godown.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0065_booking_warehouse_index
# Revises: 0064_booking_stock_type_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0065_booking_warehouse_index"
down_revision: str | None = "0064_booking_stock_type_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_booking_warehouse_dates", "booking", ["warehouse_id", "start_date"])


def downgrade() -> None:
    op.drop_index("ix_booking_warehouse_dates", table_name="booking")
