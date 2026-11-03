# ---------------------------------------------------------------
# Add column city.district_id (empty for now).
# DSQL can't add a column together with NOT NULL or a foreign key, so
# those rules are added by later migrations, after the data is filled.
#
# Revision ID: 0009_add_city_district_id
# Revises: 0008_create_district
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0009_add_city_district_id"
down_revision: str | None = "0008_create_district"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """New nullable column; filled by the next migration."""
    op.add_column("city", sa.Column("district_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    """Remove the column."""
    op.drop_column("city", "district_id")
