# ---------------------------------------------------------------
# Require city.district_id (a CHECK instead of NOT NULL).
# DSQL has no ALTER COLUMN SET NOT NULL, so a CHECK constraint does the
# same job. Added NOT VALID on DSQL; existing rows are checked by 0016.
#
# Revision ID: 0012_add_city_district_required
# Revises: 0011_add_city_district_fk
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0012_add_city_district_required"
down_revision: str | None = "0011_add_city_district_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Every city/town must have a district."""
    op.create_check_constraint("ck_city_district_required", "city", "district_id IS NOT NULL")


def downgrade() -> None:
    """Remove the check."""
    op.drop_constraint("ck_city_district_required", "city", type_="check")
