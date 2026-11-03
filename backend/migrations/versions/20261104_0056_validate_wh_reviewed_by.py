# ---------------------------------------------------------------
# Validate fk_warehouse_reviewed_by on existing rows (DSQL, async).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0056_validate_wh_reviewed_by
# Revises: 0055_warehouse_reviewed_by_fk
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0056_validate_wh_reviewed_by"
down_revision: str | None = "0055_warehouse_reviewed_by_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def is_dsql() -> bool:
    """True when migrating Aurora DSQL (local Postgres validates on its own)."""
    return op.get_bind().dialect.name == "auroradsql"


def upgrade() -> None:
    if is_dsql():
        op.execute("ALTER TABLE ASYNC warehouse VALIDATE CONSTRAINT fk_warehouse_reviewed_by")


def downgrade() -> None:
    """Nothing to undo: validating doesn't change the schema."""
