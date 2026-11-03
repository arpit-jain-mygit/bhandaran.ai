# ---------------------------------------------------------------
# A user's city must be a real city (FK, created NOT VALID on DSQL).
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0033_app_user_city_fk
# Revises: 0032_app_user_invited_by
# Created: 2026-11-04
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0033_app_user_city_fk"
down_revision: str | None = "0032_app_user_invited_by"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key("fk_app_user_city", "app_user", "city", ["city_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_app_user_city", "app_user", type_="foreignkey")
