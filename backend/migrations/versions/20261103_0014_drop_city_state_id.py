# ---------------------------------------------------------------
# Drop city.state_id - a city's state now comes from its district.
# Dropping the column also drops its old constraints (fk_city_state,
# uq_city_state_name).
#
# Revision ID: 0014_drop_city_state_id
# Revises: 0013_city_district_name_unique
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0014_drop_city_state_id"
down_revision: str | None = "0013_city_district_name_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the old direct link from city to state."""
    op.drop_column("city", "state_id")


def downgrade() -> None:
    """Re-add the column (empty; 0010's downgrade refills it). The old
    foreign key / unique rules on it are not recreated."""
    op.add_column("city", sa.Column("state_id", sa.Uuid(), nullable=True))
