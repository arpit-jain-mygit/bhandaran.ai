# ---------------------------------------------------------------
# Create table "district" - each district belongs to one state.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0008_create_district
# Revises: 0007_seed_master_data
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0008_create_district"
down_revision: str | None = "0007_seed_master_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the table with an inline foreign key to state and a
    unique (state_id, name) rule - still ONE statement."""
    op.create_table(
        "district",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "state_id",
            sa.Uuid(),
            sa.ForeignKey("state.id", name="fk_district_state"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("state_id", "name", name="uq_district_state_name"),
    )


def downgrade() -> None:
    """Remove the table."""
    op.drop_table("district")
