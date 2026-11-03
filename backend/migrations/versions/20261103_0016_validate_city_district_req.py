# ---------------------------------------------------------------
# Check existing rows against ck_city_district_required (DSQL only).
# Runs as a background job in DSQL; no-op on local Postgres.
#
# Revision ID: 0016_validate_city_district_req
# Revises: 0015_validate_city_district_fk
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0016_validate_city_district_req"
down_revision: str | None = "0015_validate_city_district_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def is_dsql() -> bool:
    """True when migrating Aurora DSQL (local Postgres validates on its own)."""
    return op.get_bind().dialect.name == "auroradsql"


def upgrade() -> None:
    if is_dsql():
        op.execute("ALTER TABLE ASYNC city VALIDATE CONSTRAINT ck_city_district_required")


def downgrade() -> None:
    """Nothing to undo: validating doesn't change the schema."""
