# ---------------------------------------------------------------
# Create booking: space a renter books in a godown (M8). Starts as
# PENDING_RENTER_CONFIRMATION or CONFIRMED, per the booking rules.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0060_create_booking
# Revises: 0059_validate_warehouse_status
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0060_create_booking"
down_revision: str | None = "0059_validate_warehouse_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "booking",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("renter_id", sa.Uuid(), nullable=False),
        sa.Column("stock_type_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rate_per_unit_month", sa.Numeric(12, 2), nullable=False),
        sa.Column("channel", sa.String(10), server_default="OFFLINE", nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("unverified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("confirmation_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('PENDING_RENTER_CONFIRMATION', 'CONFIRMED', 'ACTIVE')",
            name="ck_booking_status",
        ),
        sa.CheckConstraint("channel IN ('OFFLINE', 'ONLINE')", name="ck_booking_channel"),
        sa.CheckConstraint("quantity > 0", name="ck_booking_quantity_positive"),
        sa.CheckConstraint("end_date >= start_date", name="ck_booking_dates"),
        sa.CheckConstraint("rate_per_unit_month >= 0", name="ck_booking_rate_not_negative"),
    )


def downgrade() -> None:
    op.drop_table("booking")
