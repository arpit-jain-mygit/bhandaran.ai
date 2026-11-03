# ---------------------------------------------------------------
# Create warehouse: an owner's godown listing (M5). Starts as DRAFT.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0040_create_warehouse
# Revises: 0039_validate_app_user_status
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0040_create_warehouse"
down_revision: str | None = "0051_create_email_suppression"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "warehouse",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("address", sa.String(300), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("pincode", sa.String(6), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("storage_type_id", sa.Uuid(), nullable=False),
        sa.Column("price_per_unit_month", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("status IN ('DRAFT', 'PENDING_REVIEW')", name="ck_warehouse_status"),
        sa.CheckConstraint("capacity > 0", name="ck_warehouse_capacity_positive"),
        sa.CheckConstraint("price_per_unit_month >= 0", name="ck_warehouse_price_not_negative"),
    )


def downgrade() -> None:
    op.drop_table("warehouse")
