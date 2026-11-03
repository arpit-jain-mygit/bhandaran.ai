# ---------------------------------------------------------------
# booking.owner_id must point at a real app_user row (FK). The table is new,
# so there are no existing rows to validate.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0062_booking_owner_fk
# Revises: 0061_booking_warehouse_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0062_booking_owner_fk"
down_revision: str | None = "0061_booking_warehouse_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key("fk_booking_owner", "booking", "app_user", ["owner_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_booking_owner", "booking", type_="foreignkey")
