# ---------------------------------------------------------------
# Check existing rows against fk_city_district (DSQL only).
# Runs as a background job in DSQL; no-op on local Postgres, which
# already checked the rows when 0011 added the constraint.
#
# Revision ID: 0015_validate_city_district_fk
# Revises: 0014_drop_city_state_id
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0015_validate_city_district_fk"
down_revision: str | None = "0014_drop_city_state_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def is_dsql() -> bool:
    """True when migrating Aurora DSQL (local Postgres validates on its own)."""
    return op.get_bind().dialect.name == "auroradsql"


def upgrade() -> None:
    if is_dsql():
        op.execute("ALTER TABLE ASYNC city VALIDATE CONSTRAINT fk_city_district")


def downgrade() -> None:
    """Nothing to undo: validating doesn't change the schema."""
