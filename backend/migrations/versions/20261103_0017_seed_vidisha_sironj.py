# ---------------------------------------------------------------
# Data step (DML only): add Madhya Pradesh > Vidisha > Sironj.
# Safe to re-run: skips anything that already exists (for example
# if an admin added it by hand first).
#
# Revision ID: 0017_seed_vidisha_sironj
# Revises: 0016_validate_city_district_req
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0017_seed_vidisha_sironj"
down_revision: str | None = "0016_validate_city_district_req"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATE_CODE = "MP"
DISTRICT = "Vidisha"
TOWNS = ["Sironj"]


def upgrade() -> None:
    # District, unless it already exists in this state (any letter case).
    op.execute(
        sa.text(
            "INSERT INTO district (state_id, name) "
            "SELECT s.id, :district FROM state s WHERE s.code = :code "
            "AND NOT EXISTS (SELECT 1 FROM district d "
            "WHERE d.state_id = s.id AND lower(d.name) = lower(:district))"
        ).bindparams(district=DISTRICT, code=STATE_CODE)
    )

    # Towns in that district, unless already present.
    for town in TOWNS:
        op.execute(
            sa.text(
                "INSERT INTO city (district_id, name) "
                "SELECT d.id, :town FROM district d JOIN state s ON s.id = d.state_id "
                "WHERE s.code = :code AND lower(d.name) = lower(:district) "
                "AND NOT EXISTS (SELECT 1 FROM city c "
                "WHERE c.district_id = d.id AND lower(c.name) = lower(:town))"
            ).bindparams(town=town, district=DISTRICT, code=STATE_CODE)
        )


def downgrade() -> None:
    # Remove the towns, then the district if nothing else points at it.
    for town in TOWNS:
        op.execute(
            sa.text(
                "DELETE FROM city WHERE name = :town AND district_id IN ("
                "  SELECT d.id FROM district d JOIN state s ON s.id = d.state_id "
                "  WHERE s.code = :code AND d.name = :district)"
            ).bindparams(town=town, district=DISTRICT, code=STATE_CODE)
        )
    op.execute(
        sa.text(
            "DELETE FROM district d USING state s WHERE s.id = d.state_id "
            "AND s.code = :code AND d.name = :district "
            "AND NOT EXISTS (SELECT 1 FROM city c WHERE c.district_id = d.id)"
        ).bindparams(district=DISTRICT, code=STATE_CODE)
    )
