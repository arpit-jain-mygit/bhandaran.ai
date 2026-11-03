# ---------------------------------------------------------------
# Data step (DML only): create districts and link every existing
# city/town to one.
#
#   1. Seeded cities get their real district (Mumbai -> Mumbai City).
#   2. Any other city (e.g. added by an admin) gets a district with
#      the same name in the same state; admins can rename it later.
#
# Revision ID: 0010_backfill_city_districts
# Revises: 0009_add_city_district_id
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0010_backfill_city_districts"
down_revision: str | None = "0009_add_city_district_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (state code, city name, district name) for the cities seeded in 0007.
SEEDED_CITY_DISTRICTS = [
    ("MP", "Indore", "Indore"),
    ("MP", "Bhopal", "Bhopal"),
    ("MP", "Ujjain", "Ujjain"),
    ("MP", "Gwalior", "Gwalior"),
    ("MP", "Jabalpur", "Jabalpur"),
    ("MH", "Mumbai", "Mumbai City"),
    ("MH", "Pune", "Pune"),
    ("MH", "Nagpur", "Nagpur"),
    ("MH", "Nashik", "Nashik"),
    ("UP", "Lucknow", "Lucknow"),
    ("UP", "Kanpur", "Kanpur Nagar"),
    ("UP", "Agra", "Agra"),
    ("RJ", "Jaipur", "Jaipur"),
    ("RJ", "Kota", "Kota"),
    ("GJ", "Ahmedabad", "Ahmedabad"),
    ("GJ", "Rajkot", "Rajkot"),
    ("PB", "Ludhiana", "Ludhiana"),
    ("PB", "Amritsar", "Amritsar"),
    ("HR", "Karnal", "Karnal"),
    ("DL", "Delhi", "New Delhi"),
    ("KA", "Bengaluru", "Bengaluru Urban"),
    ("TN", "Chennai", "Chennai"),
    ("TS", "Hyderabad", "Hyderabad"),
    ("WB", "Kolkata", "Kolkata"),
    ("BR", "Patna", "Patna"),
]


def upgrade() -> None:
    # 1a. Create the real districts for seeded cities (skip if present).
    for state_code, _city, district in SEEDED_CITY_DISTRICTS:
        op.execute(
            sa.text(
                "INSERT INTO district (state_id, name) "
                "SELECT s.id, :district FROM state s WHERE s.code = :code "
                "AND NOT EXISTS (SELECT 1 FROM district d "
                "WHERE d.state_id = s.id AND d.name = :district)"
            ).bindparams(district=district, code=state_code)
        )

    # 1b. Link each seeded city to its district.
    for state_code, city, district in SEEDED_CITY_DISTRICTS:
        op.execute(
            sa.text(
                "UPDATE city SET district_id = ("
                "  SELECT d.id FROM district d JOIN state s ON s.id = d.state_id "
                "  WHERE s.code = :code AND d.name = :district) "
                "WHERE district_id IS NULL AND name = :city "
                "AND state_id = (SELECT id FROM state WHERE code = :code)"
            ).bindparams(city=city, district=district, code=state_code)
        )

    # 2a. Any city still without a district: same-name district.
    op.execute(
        "INSERT INTO district (state_id, name) "
        "SELECT DISTINCT c.state_id, c.name FROM city c "
        "WHERE c.district_id IS NULL AND NOT EXISTS ("
        "  SELECT 1 FROM district d WHERE d.state_id = c.state_id AND d.name = c.name)"
    )

    # 2b. ...and link them.
    op.execute(
        "UPDATE city c SET district_id = ("
        "  SELECT d.id FROM district d WHERE d.state_id = c.state_id AND d.name = c.name) "
        "WHERE c.district_id IS NULL"
    )


def downgrade() -> None:
    # Copy each city's state back from its district (the state_id
    # column was re-added by 0014's downgrade), then unlink and remove
    # all districts. The district table itself is dropped by 0008.
    op.execute(
        "UPDATE city c SET state_id = ("
        "  SELECT d.state_id FROM district d WHERE d.id = c.district_id)"
    )
    op.execute("UPDATE city SET district_id = NULL")
    op.execute("DELETE FROM district")
