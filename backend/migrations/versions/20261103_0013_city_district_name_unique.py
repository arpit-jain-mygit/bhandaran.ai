# ---------------------------------------------------------------
# Unique (district_id, name) for city/town names.
# The same town name can exist in two districts, but not twice in one.
# On DSQL the dialect creates it with CREATE UNIQUE INDEX ASYNC.
#
# Revision ID: 0013_city_district_name_unique
# Revises: 0012_add_city_district_required
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0013_city_district_name_unique"
down_revision: str | None = "0012_add_city_district_required"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No duplicate town names inside one district."""
    op.create_index("uq_city_district_name", "city", ["district_id", "name"], unique=True)


def downgrade() -> None:
    """Remove the index."""
    op.drop_index("uq_city_district_name", table_name="city")
