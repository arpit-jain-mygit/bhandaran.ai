# ---------------------------------------------------------------
# Create table "state" - Indian states and union territories.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0005_create_state
# Revises: 0004_create_unit
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0005_create_state"
down_revision: str | None = "0004_create_unit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the table (unique code is declared inline, so no extra DDL)."""
    op.create_table(
        "state",
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
        sa.UniqueConstraint("code", name="uq_state_code"),
    )


def downgrade() -> None:
    """Remove the table."""
    op.drop_table("state")
