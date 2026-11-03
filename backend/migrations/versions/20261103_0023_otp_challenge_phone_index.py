# ---------------------------------------------------------------
# Index otp_challenge (phone, created_at).
# Speeds up "latest code for this phone" and the hourly request limit.
# On DSQL the dialect creates it with CREATE INDEX ASYNC.
#
# Revision ID: 0023_otp_challenge_phone_index
# Revises: 0022_create_otp_challenge
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0023_otp_challenge_phone_index"
down_revision: str | None = "0022_create_otp_challenge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_otp_challenge_phone_created", "otp_challenge", ["phone", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_otp_challenge_phone_created", table_name="otp_challenge")
