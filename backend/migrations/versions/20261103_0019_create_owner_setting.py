# ---------------------------------------------------------------
# Create table "owner_setting" - per-owner overrides (M2).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0019_create_owner_setting
# Revises: 0018_create_platform_setting
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0019_create_owner_setting"
down_revision: str | None = "0018_create_platform_setting"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    One row per (owner, setting) the owner changed. owner_id has no
    foreign key yet: the owner table arrives in M3/M4.
    """
    op.create_table(
        "owner_setting",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("owner_id", "key", name="uq_owner_setting_owner_key"),
    )


def downgrade() -> None:
    """Remove the table."""
    op.drop_table("owner_setting")
