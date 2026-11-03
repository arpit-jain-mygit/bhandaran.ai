# ---------------------------------------------------------------
# Create email_suppression: addresses that bounced or complained (bounce handling).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0051_create_email_suppression
# Revises: 0050_warehouse_photo_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0051_create_email_suppression"
down_revision: str | None = "0039_validate_app_user_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_suppression",
        sa.Column("email", sa.String(254), primary_key=True),
        sa.Column("reason", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("reason IN ('BOUNCE', 'COMPLAINT')", name="ck_email_suppression_reason"),
    )


def downgrade() -> None:
    op.drop_table("email_suppression")
