# ---------------------------------------------------------------
# Baseline: the starting point of the database history.
#
# It changes nothing itself. Running it proves the migration setup
# works: Alembic creates its "alembic_version" table and records
# this revision. Real tables arrive from M1 (master data) onwards.
#
# Revision ID: 0001_baseline
# Revises: (none - first migration)
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

# Identifiers Alembic uses to order migrations.
revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Nothing to create yet."""
    pass


def downgrade() -> None:
    """Nothing to undo."""
    pass
