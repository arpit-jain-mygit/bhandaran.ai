# ---------------------------------------------------------------
# Create table "app_user" - one row per phone number (M3).
# One DDL statement per migration (Aurora DSQL rule). The unique phone
# and the status CHECK are declared inline, so it stays one statement.
#
# Revision ID: 0020_create_app_user
# Revises: 0019_create_owner_setting
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0020_create_app_user"
down_revision: str | None = "0019_create_owner_setting"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("phone", name="uq_app_user_phone"),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED')", name="ck_app_user_status"),
    )


def downgrade() -> None:
    op.drop_table("app_user")
