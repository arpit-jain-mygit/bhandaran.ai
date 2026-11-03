# ---------------------------------------------------------------
# Create table "user_role" - roles held by each user (M3).
# One DDL statement per migration (Aurora DSQL rule). Foreign key,
# unique (user_id, role) and role CHECK are inline.
#
# Revision ID: 0021_create_user_role
# Revises: 0020_create_app_user
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0021_create_user_role"
down_revision: str | None = "0020_create_app_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_role",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("app_user.id", name="fk_user_role_user"),
            nullable=False,
        ),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "role", name="uq_user_role_user_role"),
        sa.CheckConstraint("role IN ('OWNER', 'RENTER', 'ADMIN')", name="ck_user_role_role"),
    )


def downgrade() -> None:
    op.drop_table("user_role")
