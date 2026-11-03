# ---------------------------------------------------------------
# ${message}
#
# Revision ID: ${up_revision}
# Revises: ${down_revision | comma,n}
# Created: ${create_date}
#
# DSQL reminder: ONE schema change per migration; create indexes
# with CREATE INDEX ASYNC (the auroradsql dialect does this for you).
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# Identifiers Alembic uses to order migrations.
revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Apply this change."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Undo this change."""
    ${downgrades if downgrades else "pass"}
