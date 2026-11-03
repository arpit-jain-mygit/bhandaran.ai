# ---------------------------------------------------------------
# Validate ck_app_user_status on existing rows (DSQL, async).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0039_validate_app_user_status
# Revises: 0038_app_user_status_unclaimed
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0039_validate_app_user_status"
down_revision: str | None = "0038_app_user_status_unclaimed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def is_dsql() -> bool:
    """True when migrating Aurora DSQL (local Postgres validates on its own)."""
    return op.get_bind().dialect.name == "auroradsql"


def upgrade() -> None:
    if is_dsql():
        op.execute("ALTER TABLE ASYNC app_user VALIDATE CONSTRAINT ck_app_user_status")


def downgrade() -> None:
    """Nothing to undo: validating doesn't change the schema."""
