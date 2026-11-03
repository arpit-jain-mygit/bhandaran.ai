# ---------------------------------------------------------------
# Drop the phone-based otp_challenge table. Its rows are short-lived
# login codes (5 minutes), so nothing needs to be kept.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0027_drop_otp_challenge
# Revises: 0026_app_user_email_unique
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0027_drop_otp_challenge"
down_revision: str | None = "0026_app_user_email_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("otp_challenge")


def downgrade() -> None:
    # Codes expire in 5 minutes, so the old rows are not restored.
    pass
