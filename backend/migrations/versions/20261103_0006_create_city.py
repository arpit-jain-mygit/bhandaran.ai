# ---------------------------------------------------------------
# Create table "city" - each city belongs to one state.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0006_create_city
# Revises: 0005_create_state
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0006_create_city"
down_revision: str | None = "0005_create_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Create the table. Declared inline (still ONE statement):
      - foreign key to state (a city must belong to a real state)
      - unique (state_id, name), which also speeds up "cities of a state"
    """
    op.create_table(
        "city",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "state_id", sa.Uuid(), sa.ForeignKey("state.id", name="fk_city_state"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("state_id", "name", name="uq_city_state_name"),
    )


def downgrade() -> None:
    """Remove the table."""
    op.drop_table("city")
