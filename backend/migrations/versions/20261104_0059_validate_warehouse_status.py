# ---------------------------------------------------------------
# Validate ck_warehouse_status on existing rows (DSQL, async).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0059_validate_warehouse_status
# Revises: 0058_warehouse_status_approved
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0059_validate_warehouse_status"
down_revision: str | None = "0058_warehouse_status_approved"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def is_dsql() -> bool:
    """True when migrating Aurora DSQL (local Postgres validates on its own)."""
    return op.get_bind().dialect.name == "auroradsql"


def upgrade() -> None:
    if is_dsql():
        op.execute("ALTER TABLE ASYNC warehouse VALIDATE CONSTRAINT ck_warehouse_status")


def downgrade() -> None:
    """Nothing to undo: validating doesn't change the schema."""
