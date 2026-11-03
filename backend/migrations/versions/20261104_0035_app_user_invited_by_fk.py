# ---------------------------------------------------------------
# The inviting owner must be a real user (FK, NOT VALID on DSQL).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0035_app_user_invited_by_fk
# Revises: 0034_validate_app_user_city
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0035_app_user_invited_by_fk"
down_revision: str | None = "0034_validate_app_user_city"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_app_user_invited_by", "app_user", "app_user", ["invited_by_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_app_user_invited_by", "app_user", type_="foreignkey")
