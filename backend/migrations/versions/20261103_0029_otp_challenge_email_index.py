# ---------------------------------------------------------------
# Index otp_challenge (email, created_at): latest code and hourly limit.
# On DSQL the dialect creates it with CREATE INDEX ASYNC.
# One DDL statement per migration (Aurora DSQL rule).
#
# Revision ID: 0029_otp_challenge_email_index
# Revises: 0028_create_otp_challenge_email
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0029_otp_challenge_email_index"
down_revision: str | None = "0028_create_otp_challenge_email"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_otp_challenge_email_created", "otp_challenge", ["email", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_otp_challenge_email_created", table_name="otp_challenge")
