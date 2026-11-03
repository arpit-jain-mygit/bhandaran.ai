# ---------------------------------------------------------------
# Create table "unit" - how space is measured/priced: Bag, Sq ft.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0004_create_unit
# Revises: 0003_create_storage_type
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0004_create_unit"
down_revision: str | None = "0003_create_storage_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the table (unique code is declared inline, so no extra DDL)."""
    op.create_table(
        "unit",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("code", name="uq_unit_code"),
    )


def downgrade() -> None:
    """Remove the table."""
    op.drop_table("unit")
