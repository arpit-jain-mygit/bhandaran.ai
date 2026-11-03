# ---------------------------------------------------------------
# Create table "platform_setting" - admin-chosen platform values (M2).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0018_create_platform_setting
# Revises: 0017_seed_vidisha_sironj
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0018_create_platform_setting"
down_revision: str | None = "0017_seed_vidisha_sironj"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """One row per setting the admin changed from its code default."""
    op.create_table(
        "platform_setting",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    """Remove the table."""
    op.drop_table("platform_setting")
