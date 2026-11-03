# ---------------------------------------------------------------
# Foreign key city.district_id -> district.id.
# On DSQL the dialect adds it as NOT VALID (checked for new rows at once;
# existing rows are checked by 0015).
#
# Revision ID: 0011_add_city_district_fk
# Revises: 0010_backfill_city_districts
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0011_add_city_district_fk"
down_revision: str | None = "0010_backfill_city_districts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """A city/town must point at a real district."""
    op.create_foreign_key("fk_city_district", "city", "district", ["district_id"], ["id"])


def downgrade() -> None:
    """Remove the foreign key."""
    op.drop_constraint("fk_city_district", "city", type_="foreignkey")
