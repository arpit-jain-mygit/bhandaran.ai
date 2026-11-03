# ---------------------------------------------------------------
# Create warehouse_photo: listing photos stored in S3 (M5).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0049_create_warehouse_photo
# Revises: 0048_warehouse_stock_st_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0049_create_warehouse_photo"
down_revision: str | None = "0048_warehouse_stock_st_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "warehouse_photo",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("s3_key", sa.String(255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        # PENDING until the upload is confirmed by checking S3.
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("status IN ('PENDING', 'UPLOADED')", name="ck_warehouse_photo_status"),
    )


def downgrade() -> None:
    op.drop_table("warehouse_photo")
